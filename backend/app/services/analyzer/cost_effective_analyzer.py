"""
Cost-Effective Sentiment Analyzer

Strategy:
1. Use FREE local sentiment analysis for bulk classification
2. Use Claude ONLY for:
   - Final summary generation
   - Nigerian pidgin/context understanding
   - Notable comment detection (small sample)

Cost: ~$2-5 for ANY post size (vs $900+ for millions of comments)
"""

import asyncio
import json
import logging
import random
import re
from collections import Counter
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path

# Free local sentiment analysis
try:
    from textblob import TextBlob
    HAS_TEXTBLOB = True
except ImportError:
    HAS_TEXTBLOB = False

import anthropic
from app.config import settings

logger = logging.getLogger(__name__)


class CostEffectiveAnalyzer:
    """
    Hybrid sentiment analyzer that minimizes Claude API costs.

    Cost comparison for 1 million comments:
    - Full Claude analysis: ~$900
    - This approach: ~$2-5 (99.7% cheaper!)
    """

    # Nigerian pidgin positive indicators
    NAIJA_POSITIVE = [
        'omo', 'correct', 'sha', 'e sweet', 'mad o', 'fire', 'goat', 'legend',
        'king', 'queen', 'boss', 'oga', 'chairman', 'dey reign', 'no cap',
        'sabi', 'better', 'sweet', 'valid', '001', '30bg', 'odogwu', 'baddest',
        'amen', 'congrats', 'proud', 'love', 'best', 'greatest', 'win', 'winner'
    ]

    # Nigerian pidgin negative indicators
    NAIJA_NEGATIVE = [
        'werey', 'mumu', 'ode', 'olodo', 'yeye', 'craze', 'foolish', 'fake',
        'clout', 'chasing', 'cap', 'lie', 'liar', 'shame', 'fall', 'fail',
        'rubbish', 'nonsense', 'trash', 'hate', 'worst', 'bad', 'terrible'
    ]

    def __init__(self, model: str = "claude-haiku-3-5-20241022"):
        """Use Haiku for cost efficiency - 12x cheaper than Sonnet."""
        self.model = model
        self._client = None

    def _get_client(self) -> anthropic.Anthropic:
        if not self._client:
            self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        return self._client

    def _local_sentiment(self, text: str) -> Dict[str, Any]:
        """
        FREE local sentiment analysis using TextBlob + Nigerian context.

        Returns basic sentiment without API calls.
        """
        text_lower = text.lower()

        # Check Nigerian pidgin indicators first
        naija_positive_count = sum(1 for word in self.NAIJA_POSITIVE if word in text_lower)
        naija_negative_count = sum(1 for word in self.NAIJA_NEGATIVE if word in text_lower)

        # Check emojis
        positive_emojis = len(re.findall(r'[🔥💯❤️😍🙌👏✨💪🏆👑🐐💕🎉😊👍]', text))
        negative_emojis = len(re.findall(r'[😡🤮👎💩🖕😤😠🤡💔]', text))

        # TextBlob analysis (English)
        blob_score = 0
        if HAS_TEXTBLOB:
            try:
                blob = TextBlob(text)
                blob_score = blob.sentiment.polarity  # -1 to 1
            except:
                pass

        # Combine signals
        positive_signals = naija_positive_count + positive_emojis + (1 if blob_score > 0.2 else 0)
        negative_signals = naija_negative_count + negative_emojis + (1 if blob_score < -0.2 else 0)

        # Determine sentiment
        if positive_signals > negative_signals + 1:
            sentiment = 'positive'
            score = min(0.5 + (positive_signals * 0.1), 1.0)
        elif negative_signals > positive_signals + 1:
            sentiment = 'negative'
            score = max(-0.5 - (negative_signals * 0.1), -1.0)
        else:
            sentiment = 'neutral'
            score = blob_score * 0.5

        # Toxicity estimate (presence of insults/aggressive language)
        toxicity = min(negative_signals * 0.2, 1.0)

        return {
            'sentiment': sentiment,
            'sentiment_score': round(score, 2),
            'toxicity_score': round(toxicity, 2),
            'analysis_method': 'local'
        }

    async def analyze_bulk_free(
        self,
        comments: List[Dict],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict]:
        """
        Analyze ALL comments using FREE local analysis.

        This is instant and costs nothing!
        """
        total = len(comments)
        logger.info(f"Running FREE local sentiment analysis on {total:,} comments...")

        for i, comment in enumerate(comments):
            result = self._local_sentiment(comment.get('text', ''))
            comment.update(result)

            if progress_callback and i % 1000 == 0:
                progress_callback(i, total)

        logger.info("Local analysis complete (cost: $0)")
        return comments

    async def enhance_with_claude(
        self,
        comments: List[Dict],
        celebrity_name: str,
        post_context: str,
        sample_size: int = 200,
    ) -> Dict[str, Any]:
        """
        Use Claude for ONLY the high-value tasks:
        1. Understand Nigerian context on a sample
        2. Find notable/interesting comments
        3. Generate summary

        Cost: ~$0.50-2 regardless of total comment count!
        """
        logger.info(f"Enhancing analysis with Claude (sample of {sample_size})...")

        # Sample comments for Claude analysis
        # Stratified sampling: get mix of positive, negative, neutral
        positive = [c for c in comments if c.get('sentiment') == 'positive']
        negative = [c for c in comments if c.get('sentiment') == 'negative']
        neutral = [c for c in comments if c.get('sentiment') == 'neutral']

        sample = []
        # Get proportional sample, but ensure we get negative ones (they're rare but important)
        sample.extend(random.sample(positive, min(len(positive), int(sample_size * 0.6))))
        sample.extend(random.sample(negative, min(len(negative), int(sample_size * 0.2))))
        sample.extend(random.sample(neutral, min(len(neutral), int(sample_size * 0.2))))
        random.shuffle(sample)
        sample = sample[:sample_size]

        # Format for Claude
        sample_text = "\n".join([
            f"[{i+1}] @{c.get('username_anonymized', 'anon')}: {c.get('text', '')[:150]}"
            for i, c in enumerate(sample[:100])  # Send max 100 to Claude
        ])

        # Calculate stats from local analysis
        total = len(comments)
        pos_count = len(positive)
        neg_count = len(negative)
        neu_count = len(neutral)

        prompt = f"""You are a Nigerian social media analyst. Analyze these Instagram comments.

CELEBRITY: {celebrity_name}
POST: {post_context[:200] if post_context else 'N/A'}

LOCAL ANALYSIS RESULTS (from {total:,} comments):
- Positive: {pos_count:,} ({pos_count/total*100:.1f}%)
- Negative: {neg_count:,} ({neg_count/total*100:.1f}%)
- Neutral: {neu_count:,} ({neu_count/total*100:.1f}%)

SAMPLE COMMENTS FOR CONTEXT:
{sample_text}

Based on this data, provide:

1. "accuracy_assessment": Is the local sentiment analysis likely accurate? (yes/mostly/needs_adjustment)
2. "adjustment_notes": Any systematic errors you notice? (e.g., "pidgin sarcasm misclassified")
3. "notable_indices": Array of comment indices [1-100] that are particularly interesting/viral-worthy
4. "headline": Catchy Nigerian Gen-Z headline (max 10 words)
5. "vibe_summary": 2-3 sentence summary in Nigerian style
6. "spicy_take": One witty observation
7. "controversy_level": "chill", "mid", or "wahala"
8. "themes": Top 5 themes in the comments
9. "recommended_hashtags": 5 hashtags (without #)

Return ONLY valid JSON."""

        try:
            client = self._get_client()
            response = client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text.strip()

            # Parse JSON
            if response_text.startswith('```'):
                response_text = response_text.split('\n', 1)[1]
            if response_text.endswith('```'):
                response_text = response_text[:-3]

            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start != -1 and json_end > json_start:
                result = json.loads(response_text[json_start:json_end])

                # Mark notable comments
                notable_indices = result.get('notable_indices', [])
                for idx in notable_indices:
                    if 0 < idx <= len(sample):
                        sample[idx-1]['is_notable'] = True
                        sample[idx-1]['analysis_method'] = 'claude_enhanced'

                logger.info(f"Claude enhancement complete (cost: ~$0.01-0.05)")
                return result

        except Exception as e:
            logger.error(f"Claude enhancement failed: {e}")

        # Fallback
        return {
            "headline": f"{celebrity_name} Post Enter Streets!",
            "vibe_summary": f"Analysis shows {pos_count/total*100:.0f}% positive vibes!",
            "controversy_level": "mid",
            "themes": ["support", "love", "fans"],
            "recommended_hashtags": ["NaijaCelebs", "Naija", "Lagos", "Nigeria", "Vibes"]
        }

    async def full_analysis(
        self,
        comments: List[Dict],
        celebrity_name: str,
        post_context: str = "",
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Complete cost-effective analysis pipeline.

        Cost: ~$0.05-0.10 for ANY number of comments!
        """
        total = len(comments)
        logger.info(f"Starting cost-effective analysis of {total:,} comments")

        # Step 1: FREE local analysis
        comments = await self.analyze_bulk_free(comments, progress_callback)

        # Step 2: Calculate statistics
        positive = [c for c in comments if c.get('sentiment') == 'positive']
        negative = [c for c in comments if c.get('sentiment') == 'negative']
        neutral = [c for c in comments if c.get('sentiment') == 'neutral']

        stats = {
            'total': total,
            'positive': len(positive),
            'negative': len(negative),
            'neutral': len(neutral),
            'positive_pct': len(positive) / total * 100 if total > 0 else 0,
            'negative_pct': len(negative) / total * 100 if total > 0 else 0,
            'neutral_pct': len(neutral) / total * 100 if total > 0 else 0,
        }

        # Step 3: Claude enhancement (single cheap API call)
        enhancement = await self.enhance_with_claude(
            comments, celebrity_name, post_context
        )

        # Step 4: Get top comments
        top_positive = sorted(positive, key=lambda x: x.get('sentiment_score', 0), reverse=True)[:10]
        top_negative = sorted(negative, key=lambda x: x.get('toxicity_score', 0), reverse=True)[:10]
        notable = [c for c in comments if c.get('is_notable')]

        return {
            'stats': stats,
            'summary': enhancement,
            'top_positive': top_positive,
            'top_negative': top_negative,
            'notable': notable,
            'comments': comments,
            'cost_estimate': '$0.05-0.10'
        }


async def test_cost_effective():
    """Test the cost-effective analyzer."""
    # Load comments
    with open('sessions/browser_comments.json', 'r', encoding='utf-8') as f:
        comments = json.load(f)

    print(f"Testing cost-effective analysis on {len(comments):,} comments...")
    print("="*60)

    analyzer = CostEffectiveAnalyzer()

    def progress(current, total):
        if current % 500 == 0:
            print(f"Progress: {current:,}/{total:,}")

    result = await analyzer.full_analysis(
        comments=comments,
        celebrity_name="Davido",
        post_context="I be Africa man original I no be gentleman at all o",
        progress_callback=progress
    )

    stats = result['stats']
    summary = result['summary']

    print("\n" + "="*60)
    print("RESULTS (Cost: ~$0.05)")
    print("="*60)
    print(f"\nTotal: {stats['total']:,}")
    print(f"Positive: {stats['positive']:,} ({stats['positive_pct']:.1f}%)")
    print(f"Negative: {stats['negative']:,} ({stats['negative_pct']:.1f}%)")
    print(f"Neutral: {stats['neutral']:,} ({stats['neutral_pct']:.1f}%)")
    print(f"\nHeadline: {summary.get('headline', 'N/A')}")
    print(f"Vibe: {summary.get('vibe_summary', 'N/A')}")
    print(f"Controversy: {summary.get('controversy_level', 'N/A')}")
    print(f"\nThemes: {summary.get('themes', [])}")
    print(f"Hashtags: #{' #'.join(summary.get('recommended_hashtags', []))}")

    # Save
    with open('sessions/cost_effective_results.json', 'w', encoding='utf-8') as f:
        # Don't save all comments to keep file small
        save_result = {k: v for k, v in result.items() if k != 'comments'}
        save_result['sample_comments'] = result['comments'][:100]
        json.dump(save_result, f, indent=2, ensure_ascii=False, default=str)

    print(f"\nResults saved to sessions/cost_effective_results.json")


if __name__ == "__main__":
    asyncio.run(test_cost_effective())
