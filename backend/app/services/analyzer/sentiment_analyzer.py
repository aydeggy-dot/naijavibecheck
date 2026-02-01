"""Sentiment analyzer using Claude AI."""

import json
import logging
from typing import Dict, List, Tuple, Optional

import anthropic

from app.config import settings

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    AI-powered sentiment analysis using Claude API.
    Optimized for Nigerian English, pidgin, and cultural context.
    """

    def __init__(self):
        self.client = None
        self.model = "claude-sonnet-4-20250514"

    def _get_client(self) -> anthropic.Anthropic:
        """Get or create Anthropic client."""
        if not self.client:
            if not settings.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY not configured")
            self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        return self.client

    async def analyze_comments_batch(
        self,
        comments: List[Dict],
        celebrity_name: str,
        post_context: str,
    ) -> List[Dict]:
        """
        Analyze a batch of comments for sentiment.

        Args:
            comments: List of comment dicts with 'text' and 'username_anonymized'
            celebrity_name: Name of the celebrity
            post_context: Caption or context of the post

        Returns:
            List of comments with analysis data added
        """
        if not comments:
            return []

        # Prepare comments for analysis (batch of up to 50)
        batch = comments[:50]
        comments_text = "\n".join(
            [
                f"[{i+1}] @{c['username_anonymized']}: {c['text']}"
                for i, c in enumerate(batch)
            ]
        )

        prompt = f"""You are analyzing Instagram comments on a Nigerian celebrity's post.

CELEBRITY: {celebrity_name}
POST CONTEXT: {post_context[:500] if post_context else 'N/A'}

COMMENTS TO ANALYZE:
{comments_text}

IMPORTANT CONTEXT:
- These comments are from Nigerian Instagram users
- Understand Nigerian Pidgin English (e.g., "na wa", "e no easy", "omo", "abeg", "wahala")
- Understand Nigerian slang and expressions
- Consider cultural context (Nigerian entertainment, music, Nollywood, etc.)
- "Drag" culture is common - harsh criticism can be entertainment
- Emojis like 🔥💯😂 often indicate support

For EACH comment, analyze and return a JSON array with:
1. "index": The comment number
2. "sentiment": "positive", "negative", or "neutral"
3. "sentiment_score": Float from -1.0 (very negative) to 1.0 (very positive)
4. "toxicity_score": Float from 0.0 (not toxic) to 1.0 (very toxic)
5. "emotion_tags": Array of emotions like ["funny", "angry", "supportive", "jealous", "sarcastic", "loving", "critical", "trolling"]
6. "is_notable": Boolean - true if this comment is particularly interesting
7. "summary": Brief 5-10 word summary of the comment's vibe

Return ONLY valid JSON array, no other text."""

        try:
            client = self._get_client()
            response = client.messages.create(
                model=self.model,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = response.content[0].text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = response_text.split('\n', 1)[1] if '\n' in response_text else response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            # Try to extract JSON from the response (Claude sometimes adds explanation)
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1

            if json_start != -1 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                analysis_results = json.loads(json_text)
            else:
                logger.error(f"No JSON array found in response: {response_text[:200]}...")
                return batch

            # Merge analysis back into comments
            for result in analysis_results:
                idx = result.get("index", 0) - 1
                if 0 <= idx < len(batch):
                    batch[idx].update(
                        {
                            "sentiment": result.get("sentiment", "neutral"),
                            "sentiment_score": result.get("sentiment_score", 0.0),
                            "toxicity_score": result.get("toxicity_score", 0.0),
                            "emotion_tags": result.get("emotion_tags", []),
                            "is_notable": result.get("is_notable", False),
                            "ai_summary": result.get("summary", ""),
                        }
                    )

            logger.info(f"Analyzed {len(batch)} comments")
            return batch

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response: {e}")
            logger.error(f"Response was: {response_text[:500] if 'response_text' in locals() else 'N/A'}...")
            return batch
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            raise

    async def get_top_comments(
        self,
        analyzed_comments: List[Dict],
        top_n: int = 3,
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Get the top N most positive and most negative/toxic comments.

        Args:
            analyzed_comments: Comments with analysis data
            top_n: Number of top comments to return

        Returns:
            Tuple of (top_positive, top_negative)
        """
        # Sort by sentiment score for positive
        sorted_by_sentiment = sorted(
            analyzed_comments,
            key=lambda x: x.get("sentiment_score", 0),
            reverse=True,
        )

        # Sort by toxicity for negative
        sorted_by_toxicity = sorted(
            analyzed_comments,
            key=lambda x: x.get("toxicity_score", 0),
            reverse=True,
        )

        # Get top positive (high sentiment, low toxicity)
        top_positive = [
            c
            for c in sorted_by_sentiment
            if c.get("sentiment") == "positive" and c.get("toxicity_score", 0) < 0.3
        ][:top_n]

        # Get top negative/toxic
        top_negative = [
            c
            for c in sorted_by_toxicity
            if c.get("toxicity_score", 0) > 0.5 or c.get("sentiment") == "negative"
        ][:top_n]

        return top_positive, top_negative

    async def generate_post_summary(
        self,
        celebrity_name: str,
        post_caption: str,
        stats: Dict,
        top_positive: List[Dict],
        top_negative: List[Dict],
    ) -> Dict:
        """
        Generate an AI summary of the overall vibe and insights.

        Args:
            celebrity_name: Name of the celebrity
            post_caption: Original post caption
            stats: Analysis statistics dict
            top_positive: Top positive comments
            top_negative: Top negative comments

        Returns:
            Dict with headline, summary, insights, etc.
        """
        positive_comments = "\n".join(
            [f"- {c['text'][:100]}" for c in top_positive]
        )
        negative_comments = "\n".join(
            [f"- {c['text'][:100]}" for c in top_negative]
        )

        prompt = f"""You are a witty Nigerian social media analyst creating content for a Gen Z audience.

CELEBRITY: {celebrity_name}
POST: {post_caption[:300] if post_caption else 'N/A'}

STATS:
- Total comments analyzed: {stats.get('total', 0)}
- Positive: {stats.get('positive_pct', 0):.1f}%
- Negative: {stats.get('negative_pct', 0):.1f}%
- Neutral: {stats.get('neutral_pct', 0):.1f}%

TOP POSITIVE VIBES:
{positive_comments or 'None'}

TOP TOXIC/NEGATIVE:
{negative_comments or 'None'}

Generate a response with:
1. "headline": Catchy, meme-worthy headline (max 10 words). Use Nigerian slang appropriately.
2. "vibe_summary": 2-3 sentence summary of the overall vibe in fun, Gen Z Nigerian style
3. "spicy_take": One witty observation about the comments (for engagement)
4. "controversy_level": "chill", "mid", or "wahala" (how heated is the discussion)
5. "recommended_hashtags": 5 relevant Nigerian Instagram hashtags (without #)

Return as JSON only."""

        try:
            client = self._get_client()
            response = client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = response.content[0].text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = response_text.split('\n', 1)[1] if '\n' in response_text else response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            # Extract JSON object
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start != -1 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                result = json.loads(json_text)
            else:
                raise ValueError(f"No JSON object found in response")

            logger.info(f"Generated summary for {celebrity_name}")
            return result

        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {
                "headline": "The vibes are in!",
                "vibe_summary": "We analyzed the comments and the results are interesting.",
                "spicy_take": "",
                "controversy_level": "mid",
                "recommended_hashtags": ["NaijaCelebs", "Naija", "Lagos"],
            }
