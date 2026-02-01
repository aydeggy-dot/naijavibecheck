"""Carousel generator for multi-slide Instagram posts."""

import logging
from typing import Dict, List, Any, Optional

from app.services.generator.image_generator import ImageGenerator
from app.services.generator.brand_config import get_brand_config, BrandConfig

logger = logging.getLogger(__name__)


class CarouselGenerator:
    """
    Generate Instagram carousels (multi-slide posts).

    Standard carousel layout:
    1. Stats overview card
    2. Top positive comments
    3. Top negative/toxic comments
    4. AI insights/summary
    """

    def __init__(self, brand: BrandConfig = None):
        self.brand = brand or get_brand_config()
        self.image_generator = ImageGenerator(self.brand)

    def generate_standard_carousel(
        self,
        celebrity_name: str,
        stats: Dict[str, Any],
        top_positive: List[Dict[str, Any]],
        top_negative: List[Dict[str, Any]],
        ai_insights: Dict[str, Any],
    ) -> List[bytes]:
        """
        Generate a standard 4-slide carousel.

        Args:
            celebrity_name: Name of the celebrity
            stats: Analysis statistics
            top_positive: Top positive comments
            top_negative: Top negative comments
            ai_insights: AI-generated insights

        Returns:
            List of PNG images as bytes
        """
        slides = []

        # Slide 1: Stats card
        headline = ai_insights.get("headline", "The vibes are in! 🔥")
        stats_slide = self.image_generator.generate_stats_card(
            celebrity_name=celebrity_name,
            stats=stats,
            headline=headline,
        )
        slides.append(stats_slide)

        # Slide 2: Top positive comments
        if top_positive:
            positive_slide = self.image_generator.generate_comments_slide(
                title="TOP POSITIVE VIBES 💚",
                comments=top_positive,
                theme="positive",
            )
            slides.append(positive_slide)

        # Slide 3: Top negative comments
        if top_negative:
            negative_slide = self.image_generator.generate_comments_slide(
                title="THE TOXIC ZONE ☠️",
                comments=top_negative,
                theme="negative",
            )
            slides.append(negative_slide)

        # Slide 4: Insights/Summary
        insights_slide = self.image_generator.generate_insights_slide(
            celebrity_name=celebrity_name,
            insights=ai_insights,
        )
        slides.append(insights_slide)

        logger.info(f"Generated {len(slides)}-slide carousel for {celebrity_name}")
        return slides

    def generate_minimal_carousel(
        self,
        celebrity_name: str,
        stats: Dict[str, Any],
        ai_insights: Dict[str, Any],
    ) -> List[bytes]:
        """
        Generate a minimal 2-slide carousel (stats + insights).

        Args:
            celebrity_name: Name of the celebrity
            stats: Analysis statistics
            ai_insights: AI-generated insights

        Returns:
            List of PNG images as bytes
        """
        slides = []

        # Slide 1: Stats card
        headline = ai_insights.get("headline", "The vibes are in! 🔥")
        stats_slide = self.image_generator.generate_stats_card(
            celebrity_name=celebrity_name,
            stats=stats,
            headline=headline,
        )
        slides.append(stats_slide)

        # Slide 2: Insights
        insights_slide = self.image_generator.generate_insights_slide(
            celebrity_name=celebrity_name,
            insights=ai_insights,
        )
        slides.append(insights_slide)

        return slides

    def generate_comments_only_carousel(
        self,
        celebrity_name: str,
        top_positive: List[Dict[str, Any]],
        top_negative: List[Dict[str, Any]],
        headline: str = "The comments are WILD 🔥",
    ) -> List[bytes]:
        """
        Generate a carousel focused on comments.

        Args:
            celebrity_name: Name of the celebrity
            top_positive: Top positive comments
            top_negative: Top negative comments
            headline: Headline for the first slide

        Returns:
            List of PNG images as bytes
        """
        slides = []

        # Intro slide with headline
        intro_stats = {
            "positive_pct": 50,
            "negative_pct": 50,
            "neutral_pct": 0,
            "total": len(top_positive) + len(top_negative),
        }
        intro_slide = self.image_generator.generate_stats_card(
            celebrity_name=celebrity_name,
            stats=intro_stats,
            headline=headline,
        )
        slides.append(intro_slide)

        # Positive comments
        if top_positive:
            positive_slide = self.image_generator.generate_comments_slide(
                title="THE LOVE 💚",
                comments=top_positive,
                theme="positive",
            )
            slides.append(positive_slide)

        # Negative comments
        if top_negative:
            negative_slide = self.image_generator.generate_comments_slide(
                title="THE HATE 💔",
                comments=top_negative,
                theme="negative",
            )
            slides.append(negative_slide)

        return slides

    def generate_controversy_carousel(
        self,
        celebrity_name: str,
        stats: Dict[str, Any],
        top_positive: List[Dict[str, Any]],
        top_negative: List[Dict[str, Any]],
        ai_insights: Dict[str, Any],
    ) -> List[bytes]:
        """
        Generate a carousel highlighting controversy.

        Best for posts with high controversy scores.

        Args:
            celebrity_name: Name of the celebrity
            stats: Analysis statistics
            top_positive: Top positive comments
            top_negative: Top negative comments
            ai_insights: AI-generated insights

        Returns:
            List of PNG images as bytes
        """
        slides = []

        # Slide 1: Controversy intro
        controversy_headline = "⚡ WAHALA DEY! ⚡"
        stats_slide = self.image_generator.generate_stats_card(
            celebrity_name=celebrity_name,
            stats=stats,
            headline=controversy_headline,
        )
        slides.append(stats_slide)

        # Interleave positive and negative for drama
        if top_positive:
            slides.append(self.image_generator.generate_comments_slide(
                title="THE SUPPORTERS 💚",
                comments=top_positive[:2],
                theme="positive",
            ))

        if top_negative:
            slides.append(self.image_generator.generate_comments_slide(
                title="THE DRAGGING 💔",
                comments=top_negative[:2],
                theme="negative",
            ))

        # Final verdict
        insights_slide = self.image_generator.generate_insights_slide(
            celebrity_name=celebrity_name,
            insights=ai_insights,
        )
        slides.append(insights_slide)

        return slides

    def select_carousel_type(
        self,
        stats: Dict[str, Any],
        ai_insights: Dict[str, Any],
    ) -> str:
        """
        Automatically select the best carousel type based on data.

        Args:
            stats: Analysis statistics
            ai_insights: AI insights

        Returns:
            Carousel type: "standard", "controversy", "minimal"
        """
        controversy_level = ai_insights.get("controversy_level", "mid")
        controversy_score = stats.get("controversy_score", 0)

        # High controversy
        if controversy_level == "wahala" or controversy_score > 70:
            return "controversy"

        # Very one-sided (either mostly positive or negative)
        positive_pct = stats.get("positive_pct", 0)
        negative_pct = stats.get("negative_pct", 0)

        if positive_pct > 75 or negative_pct > 75:
            return "minimal"

        return "standard"
