"""
Robust Sentiment Analyzer - Production Ready

Designed to:
- Handle millions of comments patiently
- Work with API rate limits gracefully
- Resume from interruptions
- Save checkpoints for large analyses
- Ensure accuracy for final publishable posts
"""

import asyncio
import json
import logging
import time
import random
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable

import anthropic

from app.config import settings

logger = logging.getLogger(__name__)


class RobustSentimentAnalyzer:
    """
    Production-ready sentiment analyzer with:
    - Exponential backoff for API rate limits
    - Progress checkpoints for resume capability
    - Batch processing with patience
    - High accuracy for publishable content
    """

    DEFAULT_CONFIG = {
        # Batch settings
        'batch_size': 30,  # Smaller batches = more reliable JSON parsing
        'checkpoint_interval': 200,  # Save every 200 comments

        # Rate limiting
        'min_delay_between_requests': 1.0,
        'max_delay_between_requests': 3.0,
        'delay_after_rate_limit': 60,  # 1 minute
        'max_delay_after_rate_limit': 600,  # 10 minutes max backoff
        'backoff_multiplier': 2.0,
        'max_retries': 10,

        # Quality settings
        'retry_failed_batches': True,
        'max_batch_retries': 3,

        # Time limits (0 = unlimited)
        'max_analysis_time_hours': 0,
    }

    def __init__(
        self,
        checkpoint_dir: Optional[Path] = None,
        config: Optional[Dict] = None,
        model: str = "claude-sonnet-4-20250514"
    ):
        self.checkpoint_dir = checkpoint_dir or Path(settings.sessions_dir) / "analysis_checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        self.model = model

        self._client = None
        self._consecutive_errors = 0
        self._current_backoff = self.config['delay_after_rate_limit']
        self._request_count = 0

    def _get_client(self) -> anthropic.Anthropic:
        """Get or create Anthropic client."""
        if not self._client:
            if not settings.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY not configured")
            self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        return self._client

    async def _smart_delay(self):
        """Apply intelligent delay between API calls."""
        delay = random.uniform(
            self.config['min_delay_between_requests'],
            self.config['max_delay_between_requests']
        )
        await asyncio.sleep(delay)
        self._request_count += 1

    async def _handle_rate_limit(self, error_msg: str = "rate_limit") -> bool:
        """Handle rate limit with exponential backoff."""
        self._consecutive_errors += 1

        backoff = min(
            self._current_backoff * (self.config['backoff_multiplier'] ** (self._consecutive_errors - 1)),
            self.config['max_delay_after_rate_limit']
        )
        jitter = random.uniform(0, backoff * 0.2)
        total_wait = backoff + jitter

        logger.warning(
            f"Rate limit hit ({error_msg}). "
            f"Waiting {total_wait/60:.1f} minutes "
            f"(attempt {self._consecutive_errors}/{self.config['max_retries']})"
        )

        await asyncio.sleep(total_wait)

        if self._consecutive_errors >= self.config['max_retries']:
            logger.error("Max retries exceeded.")
            return False
        return True

    def _reset_backoff(self):
        """Reset backoff after successful request."""
        self._consecutive_errors = 0
        self._current_backoff = self.config['delay_after_rate_limit']

    def _get_checkpoint_path(self, analysis_id: str) -> Path:
        """Get checkpoint file path."""
        return self.checkpoint_dir / f"analysis_{analysis_id}.json"

    def _save_checkpoint(
        self,
        analysis_id: str,
        analyzed_comments: List[Dict],
        pending_indices: List[int],
        metadata: Dict
    ):
        """Save analysis checkpoint."""
        checkpoint = {
            'analysis_id': analysis_id,
            'timestamp': datetime.now().isoformat(),
            'analyzed_count': len([c for c in analyzed_comments if c.get('sentiment')]),
            'total_count': len(analyzed_comments),
            'pending_indices': pending_indices,
            'metadata': metadata,
            'comments': analyzed_comments
        }

        checkpoint_path = self._get_checkpoint_path(analysis_id)
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"Checkpoint saved: {checkpoint['analyzed_count']}/{checkpoint['total_count']} analyzed")

    def _load_checkpoint(self, analysis_id: str) -> Optional[Dict]:
        """Load checkpoint if exists."""
        checkpoint_path = self._get_checkpoint_path(analysis_id)
        if checkpoint_path.exists():
            try:
                with open(checkpoint_path, 'r', encoding='utf-8') as f:
                    checkpoint = json.load(f)
                logger.info(f"Resuming analysis: {checkpoint['analyzed_count']}/{checkpoint['total_count']}")
                return checkpoint
            except Exception as e:
                logger.warning(f"Failed to load checkpoint: {e}")
        return None

    def _build_analysis_prompt(
        self,
        comments: List[Dict],
        celebrity_name: str,
        post_context: str,
        batch_indices: List[int]
    ) -> str:
        """Build the analysis prompt for Claude."""
        comments_text = "\n".join([
            f"[{idx}] @{c['username_anonymized']}: {c['text'][:200]}"
            for idx, c in zip(batch_indices, comments)
        ])

        return f"""You are analyzing Instagram comments on a Nigerian celebrity's post.

CELEBRITY: {celebrity_name}
POST CONTEXT: {post_context[:300] if post_context else 'N/A'}

COMMENTS TO ANALYZE:
{comments_text}

IMPORTANT CONTEXT:
- These are Nigerian Instagram comments
- Understand Nigerian Pidgin English (e.g., "na wa", "e no easy", "omo", "abeg", "wahala", "werey")
- Understand Nigerian slang and cultural expressions
- "001" often refers to Davido's nickname
- "30BG" is Davido's fan base name
- Consider rivalry context (Davido vs Wizkid fans)
- Emojis like 🔥💯😂🐐👑 often indicate support

For EACH comment, return a JSON array with:
1. "index": The comment number [exactly as shown in brackets]
2. "sentiment": "positive", "negative", or "neutral"
3. "sentiment_score": Float from -1.0 to 1.0
4. "toxicity_score": Float from 0.0 to 1.0
5. "emotion_tags": Array of 1-3 emotions
6. "is_notable": Boolean - true if particularly interesting
7. "summary": Brief 5-8 word summary

Return ONLY a valid JSON array. No markdown, no explanation, just the JSON array starting with [ and ending with ]."""

    async def _analyze_batch(
        self,
        comments: List[Dict],
        celebrity_name: str,
        post_context: str,
        batch_indices: List[int],
        retry_count: int = 0
    ) -> List[Dict]:
        """Analyze a single batch of comments."""
        await self._smart_delay()

        prompt = self._build_analysis_prompt(comments, celebrity_name, post_context, batch_indices)

        try:
            client = self._get_client()
            response = client.messages.create(
                model=self.model,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = response.content[0].text.strip()

            # Clean up response
            if response_text.startswith('```'):
                response_text = response_text.split('\n', 1)[1] if '\n' in response_text else response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            # Extract JSON array
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1

            if json_start != -1 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                results = json.loads(json_text)
                self._reset_backoff()
                return results
            else:
                logger.warning(f"No JSON array in response")
                if retry_count < self.config['max_batch_retries']:
                    await asyncio.sleep(2)
                    return await self._analyze_batch(
                        comments, celebrity_name, post_context, batch_indices, retry_count + 1
                    )
                return []

        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error: {e}")
            if retry_count < self.config['max_batch_retries']:
                await asyncio.sleep(2)
                return await self._analyze_batch(
                    comments, celebrity_name, post_context, batch_indices, retry_count + 1
                )
            return []

        except anthropic.RateLimitError:
            should_continue = await self._handle_rate_limit("Anthropic rate limit")
            if should_continue and retry_count < self.config['max_batch_retries']:
                return await self._analyze_batch(
                    comments, celebrity_name, post_context, batch_indices, retry_count + 1
                )
            return []

        except anthropic.APIError as e:
            logger.error(f"API error: {e}")
            should_continue = await self._handle_rate_limit(f"API error: {e}")
            if should_continue and retry_count < self.config['max_batch_retries']:
                return await self._analyze_batch(
                    comments, celebrity_name, post_context, batch_indices, retry_count + 1
                )
            return []

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []

    async def analyze_all_comments(
        self,
        comments: List[Dict],
        celebrity_name: str,
        post_context: str,
        analysis_id: Optional[str] = None,
        resume: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze ALL comments with full robustness.

        Args:
            comments: List of comment dicts with 'text' and 'username_anonymized'
            celebrity_name: Celebrity name for context
            post_context: Post caption/context
            analysis_id: Unique ID for checkpointing (uses shortcode if available)
            resume: Whether to resume from checkpoint
            progress_callback: Callback(analyzed_count, total_count)

        Returns:
            Dict with analyzed comments and statistics
        """
        analysis_id = analysis_id or f"analysis_{int(time.time())}"
        total = len(comments)
        batch_size = self.config['batch_size']

        logger.info(f"Starting analysis of {total:,} comments")
        logger.info(f"Batch size: {batch_size}, Estimated batches: {(total + batch_size - 1) // batch_size}")

        # Check for checkpoint
        all_comments = list(comments)  # Copy
        pending_indices = list(range(total))

        if resume:
            checkpoint = self._load_checkpoint(analysis_id)
            if checkpoint:
                all_comments = checkpoint['comments']
                pending_indices = checkpoint.get('pending_indices', [])
                if not pending_indices:
                    # Recalculate pending from comments without sentiment
                    pending_indices = [i for i, c in enumerate(all_comments) if not c.get('sentiment')]

        start_time = time.time()
        last_checkpoint_count = total - len(pending_indices)
        batch_count = 0

        while pending_indices:
            # Check time limit
            if self.config['max_analysis_time_hours'] > 0:
                elapsed_hours = (time.time() - start_time) / 3600
                if elapsed_hours >= self.config['max_analysis_time_hours']:
                    logger.info(f"Time limit reached: {self.config['max_analysis_time_hours']} hours")
                    break

            # Get next batch
            batch_indices = pending_indices[:batch_size]
            batch_comments = [all_comments[i] for i in batch_indices]

            batch_count += 1

            # Analyze batch
            results = await self._analyze_batch(
                batch_comments, celebrity_name, post_context, batch_indices
            )

            # Apply results
            for result in results:
                idx = result.get('index')
                if idx is not None and idx in batch_indices:
                    all_comments[idx].update({
                        'sentiment': result.get('sentiment', 'unknown'),
                        'sentiment_score': result.get('sentiment_score', 0.0),
                        'toxicity_score': result.get('toxicity_score', 0.0),
                        'emotion_tags': result.get('emotion_tags', []),
                        'is_notable': result.get('is_notable', False),
                        'ai_summary': result.get('summary', ''),
                    })
                    if idx in pending_indices:
                        pending_indices.remove(idx)

            # If batch had no results, still remove from pending to avoid infinite loop
            # but mark as failed
            if not results:
                for idx in batch_indices:
                    if idx in pending_indices:
                        all_comments[idx]['sentiment'] = 'analysis_failed'
                        pending_indices.remove(idx)

            analyzed_count = total - len(pending_indices)

            # Progress callback
            if progress_callback:
                progress_callback(analyzed_count, total)

            # Log progress
            if batch_count % 10 == 0:
                elapsed = time.time() - start_time
                rate = analyzed_count / (elapsed / 60) if elapsed > 0 else 0
                remaining = len(pending_indices)
                eta = remaining / rate if rate > 0 else 0
                logger.info(
                    f"Progress: {analyzed_count:,}/{total:,} ({analyzed_count/total*100:.1f}%) "
                    f"Rate: {rate:.0f}/min, ETA: {eta:.0f} min"
                )

            # Save checkpoint
            if analyzed_count - last_checkpoint_count >= self.config['checkpoint_interval']:
                self._save_checkpoint(
                    analysis_id, all_comments, pending_indices,
                    {'celebrity': celebrity_name, 'batch_count': batch_count}
                )
                last_checkpoint_count = analyzed_count

        # Final checkpoint
        self._save_checkpoint(
            analysis_id, all_comments, pending_indices,
            {'celebrity': celebrity_name, 'batch_count': batch_count, 'completed': len(pending_indices) == 0}
        )

        # Calculate statistics
        analyzed = [c for c in all_comments if c.get('sentiment') in ['positive', 'negative', 'neutral']]
        positive = [c for c in analyzed if c.get('sentiment') == 'positive']
        negative = [c for c in analyzed if c.get('sentiment') == 'negative']
        neutral = [c for c in analyzed if c.get('sentiment') == 'neutral']
        failed = [c for c in all_comments if c.get('sentiment') == 'analysis_failed']

        elapsed = time.time() - start_time

        stats = {
            'total_comments': total,
            'successfully_analyzed': len(analyzed),
            'positive': len(positive),
            'negative': len(negative),
            'neutral': len(neutral),
            'failed': len(failed),
            'positive_pct': (len(positive) / len(analyzed) * 100) if analyzed else 0,
            'negative_pct': (len(negative) / len(analyzed) * 100) if analyzed else 0,
            'neutral_pct': (len(neutral) / len(analyzed) * 100) if analyzed else 0,
            'analysis_time_minutes': elapsed / 60,
        }

        logger.info(
            f"Analysis complete: {stats['successfully_analyzed']:,}/{total:,} in {elapsed/60:.1f} min"
        )
        logger.info(
            f"Sentiment: {stats['positive_pct']:.1f}% positive, "
            f"{stats['negative_pct']:.1f}% negative, "
            f"{stats['neutral_pct']:.1f}% neutral"
        )

        return {
            'analysis_id': analysis_id,
            'stats': stats,
            'comments': all_comments,
        }

    async def get_top_comments(
        self,
        analyzed_comments: List[Dict],
        top_n: int = 5
    ) -> Dict[str, List[Dict]]:
        """Get top positive and negative comments."""
        analyzed = [c for c in analyzed_comments if c.get('sentiment')]

        # Top positive
        positive = sorted(
            [c for c in analyzed if c.get('sentiment') == 'positive'],
            key=lambda x: x.get('sentiment_score', 0),
            reverse=True
        )

        # Top negative/toxic
        negative = sorted(
            [c for c in analyzed if c.get('sentiment') == 'negative' or c.get('toxicity_score', 0) > 0.5],
            key=lambda x: x.get('toxicity_score', 0),
            reverse=True
        )

        # Notable comments
        notable = [c for c in analyzed if c.get('is_notable')]

        return {
            'top_positive': positive[:top_n],
            'top_negative': negative[:top_n],
            'notable': notable[:top_n * 2],
        }

    async def generate_summary(
        self,
        celebrity_name: str,
        post_caption: str,
        stats: Dict,
        top_comments: Dict,
    ) -> Dict[str, Any]:
        """Generate AI summary of the analysis."""
        positive_samples = "\n".join([
            f"- {c['text'][:100]}" for c in top_comments.get('top_positive', [])[:5]
        ])
        negative_samples = "\n".join([
            f"- {c['text'][:100]}" for c in top_comments.get('top_negative', [])[:5]
        ])

        prompt = f"""You are a witty Nigerian social media analyst creating content for Gen Z audience.

CELEBRITY: {celebrity_name}
POST: {post_caption[:300] if post_caption else 'N/A'}

ANALYSIS STATS:
- Total comments analyzed: {stats.get('successfully_analyzed', 0):,}
- Positive: {stats.get('positive_pct', 0):.1f}%
- Negative: {stats.get('negative_pct', 0):.1f}%
- Neutral: {stats.get('neutral_pct', 0):.1f}%

TOP POSITIVE COMMENTS:
{positive_samples or 'None'}

TOP NEGATIVE/TOXIC:
{negative_samples or 'None'}

Generate a response with:
1. "headline": Catchy, meme-worthy headline (max 12 words). Use Nigerian slang.
2. "vibe_summary": 2-3 sentence summary of the overall vibe in fun, Gen Z Nigerian style
3. "spicy_take": One witty observation (for engagement)
4. "controversy_level": "chill", "mid", or "wahala"
5. "key_insights": Array of 3-5 key insights
6. "recommended_hashtags": 5 relevant Nigerian hashtags (without #)

Return ONLY valid JSON, no markdown."""

        try:
            await self._smart_delay()
            client = self._get_client()
            response = client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = response.content[0].text.strip()

            # Clean and parse
            if response_text.startswith('```'):
                response_text = response_text.split('\n', 1)[1] if '\n' in response_text else response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]

            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start != -1 and json_end > json_start:
                return json.loads(response_text[json_start:json_end])

        except Exception as e:
            logger.error(f"Error generating summary: {e}")

        # Fallback
        return {
            "headline": f"{celebrity_name} Post Dey Scatter Internet",
            "vibe_summary": "The comments are in and the vibes are interesting!",
            "spicy_take": "Check the analysis for the full gist.",
            "controversy_level": "mid",
            "key_insights": [f"{stats.get('positive_pct', 0):.0f}% positive vibes"],
            "recommended_hashtags": ["NaijaCelebs", "Naija", "Lagos", "Nigeria", "Vibes"]
        }


async def test_robust_analyzer():
    """Test the robust analyzer."""
    # Load comments
    with open('sessions/browser_comments.json', 'r', encoding='utf-8') as f:
        comments = json.load(f)

    print(f"Testing with {len(comments)} comments...")

    analyzer = RobustSentimentAnalyzer()

    def progress(current, total):
        pct = (current / total * 100) if total > 0 else 0
        print(f"\rAnalyzing: {current:,}/{total:,} ({pct:.1f}%)", end="", flush=True)

    result = await analyzer.analyze_all_comments(
        comments=comments[:100],  # Test with 100
        celebrity_name='Davido',
        post_context='I be Africa man original I no be gentleman at all o',
        analysis_id='test_analysis',
        progress_callback=progress
    )

    print(f"\n\nStats: {result['stats']}")

    # Save results
    with open('sessions/robust_analysis_test.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
    print("Results saved to sessions/robust_analysis_test.json")


if __name__ == "__main__":
    asyncio.run(test_robust_analyzer())
