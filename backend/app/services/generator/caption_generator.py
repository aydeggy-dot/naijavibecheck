"""Caption generator for Instagram posts."""

import logging
from typing import Dict, List, Any, Optional

import anthropic

from app.config import settings
from app.services.generator.brand_config import get_brand_config, BrandConfig

logger = logging.getLogger(__name__)


class CaptionGenerator:
    """
    Generate engaging Instagram captions.

    Features:
    - AI-powered caption generation
    - Hashtag optimization
    - Call-to-action templates
    - Nigerian slang integration
    """

    def __init__(self, brand: BrandConfig = None):
        self.brand = brand or get_brand_config()
        self.client = None

    def _get_client(self) -> anthropic.Anthropic:
        """Get or create Anthropic client."""
        if not self.client:
            if not settings.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY not configured")
            self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        return self.client

    async def generate_caption(
        self,
        celebrity_name: str,
        stats: Dict[str, Any],
        ai_insights: Dict[str, Any],
        content_type: str = "carousel",
    ) -> Dict[str, Any]:
        """
        Generate a full caption with hashtags.

        Args:
            celebrity_name: Name of the celebrity
            stats: Analysis statistics
            ai_insights: AI-generated insights
            content_type: Type of content (carousel, image, reel)

        Returns:
            Dict with caption, hashtags, call_to_action
        """
        headline = ai_insights.get("headline", "The vibes are in!")
        vibe_summary = ai_insights.get("vibe_summary", "")
        controversy_level = ai_insights.get("controversy_level", "mid")
        recommended_hashtags = ai_insights.get("recommended_hashtags", [])

        prompt = f"""Generate an engaging Instagram caption for a Nigerian audience.

CONTEXT:
- Celebrity: {celebrity_name}
- Content type: {content_type}
- Headline: {headline}
- Vibe summary: {vibe_summary}
- Controversy level: {controversy_level}
- Stats: {stats.get('positive_pct', 0):.0f}% positive, {stats.get('negative_pct', 0):.0f}% negative
- Total comments analyzed: {stats.get('total', 0)}

REQUIREMENTS:
1. Write in a fun, Gen Z Nigerian style
2. Use Nigerian slang naturally (omo, na wa, e choke, etc.)
3. Include emojis but don't overdo it
4. Create engagement (ask a question or encourage comments)
5. Keep it under 200 words
6. Don't use the word "algorithm"

Return a JSON object with:
- "caption": The main caption text
- "call_to_action": A short engagement prompt (e.g., "Drop your take below!")
- "additional_hashtags": 3-5 relevant hashtags (without #)

Return ONLY valid JSON."""

        try:
            client = self._get_client()
            response = client.messages.create(
                model="claude-opus-4-5-20250514",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )

            import json
            result = json.loads(response.content[0].text)

            # Combine hashtags
            all_hashtags = list(set(
                recommended_hashtags +
                result.get("additional_hashtags", []) +
                self.brand.default_hashtags
            ))

            return {
                "caption": result.get("caption", self._fallback_caption(celebrity_name, stats)),
                "call_to_action": result.get("call_to_action", "What do you think? 👇"),
                "hashtags": all_hashtags[:15],  # Instagram limit consideration
            }

        except Exception as e:
            logger.error(f"Error generating caption: {e}")
            return self._generate_fallback_caption(celebrity_name, stats, ai_insights)

    def _generate_fallback_caption(
        self,
        celebrity_name: str,
        stats: Dict[str, Any],
        ai_insights: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate a fallback caption without AI."""
        headline = ai_insights.get("headline", "The vibes are in!")
        positive_pct = stats.get("positive_pct", 0)
        negative_pct = stats.get("negative_pct", 0)
        total = stats.get("total", 0)

        # Determine vibe
        if positive_pct > 60:
            vibe_text = "The love is LOUD! 💚"
        elif negative_pct > 60:
            vibe_text = "Omo, the dragging is real! 💔"
        else:
            vibe_text = "It's giving... mixed signals 🤔"

        caption = f"""🔥 {celebrity_name.upper()} VIBE CHECK 🔥

{headline}

{vibe_text}

📊 We analyzed {total:,} comments and here's what we found:
💚 {positive_pct:.0f}% positive
💔 {negative_pct:.0f}% negative
😐 {stats.get('neutral_pct', 0):.0f}% neutral

Swipe to see the most interesting comments! ➡️"""

        return {
            "caption": caption,
            "call_to_action": "What's your take? Drop it below! 👇",
            "hashtags": self.brand.default_hashtags,
        }

    def _fallback_caption(self, celebrity_name: str, stats: Dict[str, Any]) -> str:
        """Simple fallback caption."""
        return f"🔥 {celebrity_name.upper()} VIBE CHECK 🔥\n\nThe results are in! Swipe to see what people are saying. 👀"

    def build_full_caption(
        self,
        caption: str,
        call_to_action: str,
        hashtags: List[str],
    ) -> str:
        """
        Build the complete caption with formatting.

        Args:
            caption: Main caption text
            call_to_action: Engagement prompt
            hashtags: List of hashtags

        Returns:
            Formatted caption string
        """
        parts = [
            caption,
            "",  # Empty line
            call_to_action,
            "",
            f"Follow {self.brand.handle} for more! 🔥",
            "",
            ".",  # Hashtag separator
            ".",
            ".",
            "",
            " ".join([f"#{tag}" for tag in hashtags]),
        ]

        return "\n".join(parts)

    def generate_story_caption(
        self,
        celebrity_name: str,
        headline: str,
    ) -> str:
        """
        Generate a short caption for Instagram stories.

        Args:
            celebrity_name: Celebrity name
            headline: Main headline

        Returns:
            Short story caption
        """
        return f"🔥 {celebrity_name}\n\n{headline}\n\nFull breakdown in our latest post! 👇"

    def generate_reel_caption(
        self,
        celebrity_name: str,
        stats: Dict[str, Any],
        ai_insights: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate a caption optimized for Reels.

        Reels captions should be shorter and hook-focused.

        Args:
            celebrity_name: Celebrity name
            stats: Statistics
            ai_insights: AI insights

        Returns:
            Caption dict
        """
        headline = ai_insights.get("headline", "The vibes are in!")
        positive_pct = stats.get("positive_pct", 0)

        # Short, punchy caption for Reels
        if positive_pct > 70:
            hook = f"Why everyone loves {celebrity_name} 💚"
        elif positive_pct < 30:
            hook = f"Why {celebrity_name} is getting dragged 💔"
        else:
            hook = f"{celebrity_name} got the internet DIVIDED ⚡"

        caption = f"""{hook}

{headline}

Full breakdown at the end! 👀

Follow for more celeb vibe checks! 🔥"""

        return {
            "caption": caption,
            "call_to_action": "Tag someone who needs to see this! 👇",
            "hashtags": self.brand.default_hashtags[:10],
        }
