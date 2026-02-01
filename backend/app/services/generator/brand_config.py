"""Brand configuration and styling for NaijaVibeCheck."""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from pathlib import Path


@dataclass
class BrandColors:
    """Brand color palette."""

    primary: str = "#FF6B35"        # Vibrant orange
    secondary: str = "#004E89"      # Deep blue
    accent: str = "#FFBE0B"         # Yellow
    positive: str = "#2EC4B6"       # Teal/green
    negative: str = "#E71D36"       # Red
    neutral: str = "#7B8794"        # Gray
    background: str = "#1A1A2E"     # Dark purple-black
    background_alt: str = "#16213E" # Slightly lighter
    card_bg: str = "#0F3460"        # Card background
    text: str = "#FFFFFF"           # White
    text_secondary: str = "#A0A0A0" # Light gray
    text_muted: str = "#6B7280"     # Muted gray

    def to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def to_rgba(self, hex_color: str, alpha: float = 1.0) -> Tuple[int, int, int, int]:
        """Convert hex color to RGBA tuple."""
        r, g, b = self.to_rgb(hex_color)
        return (r, g, b, int(alpha * 255))


@dataclass
class BrandFonts:
    """Brand font configuration."""

    heading: str = "Arial Black"
    body: str = "Arial"
    accent: str = "Impact"

    # Font sizes
    title_size: int = 72
    heading_size: int = 48
    subheading_size: int = 36
    body_size: int = 28
    caption_size: int = 24
    small_size: int = 20


@dataclass
class BrandConfig:
    """Complete brand configuration."""

    name: str = "NaijaVibeCheck"
    handle: str = "@naijavibecheck"
    tagline: str = "The vibes don't lie 🔥"

    colors: BrandColors = field(default_factory=BrandColors)
    fonts: BrandFonts = field(default_factory=BrandFonts)

    # Image dimensions
    post_size: Tuple[int, int] = (1080, 1080)      # Square post
    portrait_size: Tuple[int, int] = (1080, 1350)  # Portrait (4:5)
    story_size: Tuple[int, int] = (1080, 1920)     # Story/Reel

    # Default hashtags
    default_hashtags: List[str] = field(default_factory=lambda: [
        "NaijaVibeCheck",
        "NaijaCelebs",
        "Naija",
        "Lagos",
        "NigeriaEntertainment",
        "Gist",
        "NaijaTwitter",
    ])

    # Emoji mappings
    sentiment_emojis: Dict[str, str] = field(default_factory=lambda: {
        "positive": "💚",
        "negative": "💔",
        "neutral": "😐",
        "fire": "🔥",
        "love": "❤️",
        "toxic": "☠️",
        "controversy": "⚡",
    })

    # Controversy level labels
    controversy_labels: Dict[str, str] = field(default_factory=lambda: {
        "low": "Chill vibes 😌",
        "medium": "Mid wahala 🤔",
        "high": "Full wahala mode 🔥",
    })


# Global brand config instance
BRAND = BrandConfig()


def get_brand_config() -> BrandConfig:
    """Get the brand configuration."""
    return BRAND
