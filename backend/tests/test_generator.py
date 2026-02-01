"""Tests for content generation services."""

import pytest
from io import BytesIO
from PIL import Image

from app.services.generator.brand_config import BrandConfig, BrandColors, get_brand_config
from app.services.generator.image_generator import ImageGenerator
from app.services.generator.carousel_generator import CarouselGenerator
from app.services.generator.caption_generator import CaptionGenerator


class TestBrandConfig:
    """Tests for brand configuration."""

    def test_default_brand_config(self):
        """Test default brand configuration."""
        brand = get_brand_config()
        assert brand.name == "NaijaVibeCheck"
        assert brand.handle == "@naijavibecheck"
        assert brand.colors.primary == "#FF6B35"

    def test_color_to_rgb(self):
        """Test hex to RGB conversion."""
        colors = BrandColors()
        rgb = colors.to_rgb("#FF6B35")
        assert rgb == (255, 107, 53)

    def test_color_to_rgba(self):
        """Test hex to RGBA conversion."""
        colors = BrandColors()
        rgba = colors.to_rgba("#FF6B35", 0.5)
        assert rgba == (255, 107, 53, 127)


class TestImageGenerator:
    """Tests for image generation."""

    def setup_method(self):
        self.generator = ImageGenerator()

    def test_generate_stats_card(self):
        """Test stats card generation."""
        stats = {
            "total": 500,
            "positive_pct": 45.0,
            "negative_pct": 30.0,
            "neutral_pct": 25.0,
        }

        image_bytes = self.generator.generate_stats_card(
            celebrity_name="Test Celebrity",
            stats=stats,
            headline="The vibes are fire! 🔥",
        )

        # Verify it's valid PNG
        assert image_bytes is not None
        assert len(image_bytes) > 0

        # Load as image to verify
        img = Image.open(BytesIO(image_bytes))
        assert img.format == "PNG"
        assert img.size == (1080, 1350)  # Portrait size

    def test_generate_comments_slide_positive(self):
        """Test positive comments slide generation."""
        comments = [
            {"username_anonymized": "user***123", "text": "This is amazing!"},
            {"username_anonymized": "fan***456", "text": "Love this so much!"},
        ]

        image_bytes = self.generator.generate_comments_slide(
            title="TOP POSITIVE VIBES 💚",
            comments=comments,
            theme="positive",
        )

        img = Image.open(BytesIO(image_bytes))
        assert img.format == "PNG"

    def test_generate_comments_slide_negative(self):
        """Test negative comments slide generation."""
        comments = [
            {"username_anonymized": "hater***789", "text": "This is terrible!"},
        ]

        image_bytes = self.generator.generate_comments_slide(
            title="THE TOXIC ZONE ☠️",
            comments=comments,
            theme="negative",
        )

        img = Image.open(BytesIO(image_bytes))
        assert img.format == "PNG"

    def test_generate_insights_slide(self):
        """Test insights slide generation."""
        insights = {
            "vibe_summary": "The vibes are mixed but leaning positive.",
            "spicy_take": "Looks like the fans are divided!",
            "controversy_level": "mid",
        }

        image_bytes = self.generator.generate_insights_slide(
            celebrity_name="Test Celebrity",
            insights=insights,
        )

        img = Image.open(BytesIO(image_bytes))
        assert img.format == "PNG"


class TestCarouselGenerator:
    """Tests for carousel generation."""

    def setup_method(self):
        self.generator = CarouselGenerator()

    def test_generate_standard_carousel(self):
        """Test standard carousel generation."""
        stats = {
            "total": 500,
            "positive_pct": 45.0,
            "negative_pct": 30.0,
            "neutral_pct": 25.0,
        }
        top_positive = [
            {"username_anonymized": "user***1", "text": "Amazing!"},
        ]
        top_negative = [
            {"username_anonymized": "user***2", "text": "Terrible!"},
        ]
        ai_insights = {
            "headline": "The vibes are in!",
            "vibe_summary": "Mixed reactions",
            "controversy_level": "mid",
        }

        slides = self.generator.generate_standard_carousel(
            celebrity_name="Test Celebrity",
            stats=stats,
            top_positive=top_positive,
            top_negative=top_negative,
            ai_insights=ai_insights,
        )

        assert len(slides) == 4  # Stats, positive, negative, insights
        for slide in slides:
            assert len(slide) > 0
            img = Image.open(BytesIO(slide))
            assert img.format == "PNG"

    def test_generate_minimal_carousel(self):
        """Test minimal carousel generation."""
        stats = {
            "total": 100,
            "positive_pct": 80.0,
            "negative_pct": 10.0,
            "neutral_pct": 10.0,
        }
        ai_insights = {"headline": "Love is in the air!"}

        slides = self.generator.generate_minimal_carousel(
            celebrity_name="Test Celebrity",
            stats=stats,
            ai_insights=ai_insights,
        )

        assert len(slides) == 2  # Stats + insights only

    def test_select_carousel_type(self):
        """Test automatic carousel type selection."""
        # High controversy
        controversy_stats = {"controversy_score": 80}
        controversy_insights = {"controversy_level": "wahala"}
        assert self.generator.select_carousel_type(
            controversy_stats, controversy_insights
        ) == "controversy"

        # Very positive
        positive_stats = {"positive_pct": 85, "controversy_score": 10}
        positive_insights = {"controversy_level": "chill"}
        assert self.generator.select_carousel_type(
            positive_stats, positive_insights
        ) == "minimal"

        # Balanced
        balanced_stats = {"positive_pct": 50, "negative_pct": 30, "controversy_score": 40}
        balanced_insights = {"controversy_level": "mid"}
        assert self.generator.select_carousel_type(
            balanced_stats, balanced_insights
        ) == "standard"


class TestCaptionGenerator:
    """Tests for caption generation."""

    def setup_method(self):
        self.generator = CaptionGenerator()

    def test_fallback_caption(self):
        """Test fallback caption generation."""
        stats = {
            "total": 500,
            "positive_pct": 45.0,
            "negative_pct": 30.0,
            "neutral_pct": 25.0,
        }
        ai_insights = {
            "headline": "The vibes are mixed!",
        }

        result = self.generator._generate_fallback_caption(
            celebrity_name="Test Celebrity",
            stats=stats,
            ai_insights=ai_insights,
        )

        assert "caption" in result
        assert "hashtags" in result
        assert "TEST CELEBRITY" in result["caption"]
        assert "500" in result["caption"]

    def test_build_full_caption(self):
        """Test full caption building."""
        caption = self.generator.build_full_caption(
            caption="This is the main caption.",
            call_to_action="What do you think?",
            hashtags=["NaijaVibeCheck", "Naija"],
        )

        assert "This is the main caption." in caption
        assert "What do you think?" in caption
        assert "#NaijaVibeCheck" in caption
        assert "@naijavibecheck" in caption

    def test_story_caption(self):
        """Test story caption generation."""
        caption = self.generator.generate_story_caption(
            celebrity_name="Test Celebrity",
            headline="The vibes are WILD!",
        )

        assert "Test Celebrity" in caption
        assert "WILD" in caption

    def test_reel_caption(self):
        """Test reel caption generation."""
        stats = {"positive_pct": 75}
        ai_insights = {"headline": "Everyone loves them!"}

        result = self.generator.generate_reel_caption(
            celebrity_name="Test Celebrity",
            stats=stats,
            ai_insights=ai_insights,
        )

        assert "caption" in result
        assert "loves" in result["caption"].lower()
