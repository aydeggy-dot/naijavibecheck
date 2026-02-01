"""Image generator for Instagram posts."""

import io
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from PIL import Image, ImageDraw, ImageFont, ImageFilter

from app.services.generator.brand_config import get_brand_config, BrandConfig
from app.config import settings

logger = logging.getLogger(__name__)


class ImageGenerator:
    """
    Generate Instagram-ready images with:
    - Statistics overlays
    - Comment spotlights
    - Vibe meters
    - Brand styling
    """

    def __init__(self, brand: BrandConfig = None):
        self.brand = brand or get_brand_config()
        self.fonts_cache: Dict[str, ImageFont.FreeTypeFont] = {}

    def generate_stats_card(
        self,
        celebrity_name: str,
        stats: Dict[str, Any],
        headline: str,
        size: Tuple[int, int] = None,
    ) -> bytes:
        """
        Generate a statistics card showing sentiment breakdown.

        Args:
            celebrity_name: Name of the celebrity
            stats: Dict with positive_pct, negative_pct, neutral_pct, total
            headline: Catchy headline for the post
            size: Image size (default: portrait 1080x1350)

        Returns:
            PNG image as bytes
        """
        size = size or self.brand.portrait_size
        width, height = size

        # Create base image with gradient background
        img = self._create_gradient_background(width, height)
        draw = ImageDraw.Draw(img)

        # Add decorative elements
        self._add_decorative_elements(img, draw)

        # Brand header
        y_pos = 60
        y_pos = self._draw_brand_header(draw, width, y_pos)

        # Celebrity name
        y_pos += 40
        font_heading = self._get_font("heading", 52)
        self._draw_centered_text(
            draw, celebrity_name.upper(), width, y_pos,
            font_heading, self.brand.colors.text
        )

        # Subtitle
        y_pos += 70
        font_sub = self._get_font("body", 28)
        self._draw_centered_text(
            draw, "📊 COMMENT VIBE CHECK", width, y_pos,
            font_sub, self.brand.colors.text_secondary
        )

        # Vibe meter
        y_pos += 60
        y_pos = self._draw_vibe_meter(
            draw, width, y_pos,
            stats.get("positive_pct", 0),
            stats.get("negative_pct", 0),
            stats.get("neutral_pct", 0),
        )

        # Stats breakdown
        y_pos += 50
        stats_items = [
            ("💚", "Positive", stats.get("positive_pct", 0), self.brand.colors.positive),
            ("💔", "Negative", stats.get("negative_pct", 0), self.brand.colors.negative),
            ("😐", "Neutral", stats.get("neutral_pct", 0), self.brand.colors.neutral),
        ]

        for emoji, label, pct, color in stats_items:
            y_pos = self._draw_stat_row(draw, emoji, label, pct, color, width, y_pos)
            y_pos += 20

        # Headline
        y_pos += 40
        font_headline = self._get_font("body", 32)
        # Wrap headline if too long
        wrapped = self._wrap_text(f'"{headline}"', font_headline, width - 120)
        for line in wrapped:
            self._draw_centered_text(
                draw, line, width, y_pos,
                font_headline, self.brand.colors.accent
            )
            y_pos += 45

        # Total comments
        y_pos += 30
        font_small = self._get_font("body", 22)
        total = stats.get("total", 0)
        self._draw_centered_text(
            draw, f"Based on {total:,} comments analyzed", width, y_pos,
            font_small, self.brand.colors.text_muted
        )

        # Brand footer
        self._draw_brand_footer(draw, width, height)

        return self._image_to_bytes(img)

    def generate_comments_slide(
        self,
        title: str,
        comments: List[Dict[str, Any]],
        theme: str = "positive",
        size: Tuple[int, int] = None,
    ) -> bytes:
        """
        Generate a slide showcasing specific comments.

        Args:
            title: Slide title (e.g., "TOP POSITIVE VIBES 💚")
            comments: List of comment dicts with username_anonymized, text
            theme: "positive" or "negative"
            size: Image size

        Returns:
            PNG image as bytes
        """
        size = size or self.brand.portrait_size
        width, height = size

        # Create background with theme color accent
        img = self._create_gradient_background(width, height)
        draw = ImageDraw.Draw(img)

        theme_color = (
            self.brand.colors.positive if theme == "positive"
            else self.brand.colors.negative
        )

        # Title
        y_pos = 80
        font_title = self._get_font("heading", 42)
        self._draw_centered_text(draw, title, width, y_pos, font_title, theme_color)

        # Comment cards
        y_pos += 80
        card_margin = 50
        card_width = width - (card_margin * 2)

        for i, comment in enumerate(comments[:3]):
            y_pos = self._draw_comment_card(
                img, draw,
                x=card_margin,
                y=y_pos,
                width=card_width,
                username=comment.get("username_anonymized", "user***"),
                text=comment.get("text", "")[:150],
                number=i + 1,
                theme=theme,
            )
            y_pos += 30

        # Brand footer
        self._draw_brand_footer(draw, width, height)

        return self._image_to_bytes(img)

    def generate_insights_slide(
        self,
        celebrity_name: str,
        insights: Dict[str, Any],
        size: Tuple[int, int] = None,
    ) -> bytes:
        """
        Generate a summary/insights slide.

        Args:
            celebrity_name: Celebrity name
            insights: AI insights dict with vibe_summary, spicy_take, etc.
            size: Image size

        Returns:
            PNG image as bytes
        """
        size = size or self.brand.portrait_size
        width, height = size

        img = self._create_gradient_background(width, height)
        draw = ImageDraw.Draw(img)
        self._add_decorative_elements(img, draw)

        # Title
        y_pos = 100
        font_title = self._get_font("heading", 42)
        self._draw_centered_text(
            draw, "THE VERDICT 🎯", width, y_pos,
            font_title, self.brand.colors.accent
        )

        # Celebrity name
        y_pos += 70
        font_name = self._get_font("body", 32)
        self._draw_centered_text(
            draw, celebrity_name, width, y_pos,
            font_name, self.brand.colors.text_secondary
        )

        # Vibe summary
        y_pos += 80
        font_summary = self._get_font("body", 28)
        summary = insights.get("vibe_summary", "The vibes are interesting...")
        wrapped = self._wrap_text(summary, font_summary, width - 100)
        for line in wrapped:
            self._draw_centered_text(draw, line, width, y_pos, font_summary, self.brand.colors.text)
            y_pos += 40

        # Controversy level
        y_pos += 50
        controversy = insights.get("controversy_level", "mid")
        controversy_label = self.brand.controversy_labels.get(controversy, "Mid wahala 🤔")

        font_controversy = self._get_font("heading", 36)
        self._draw_centered_text(
            draw, controversy_label, width, y_pos,
            font_controversy, self.brand.colors.primary
        )

        # Spicy take
        spicy_take = insights.get("spicy_take", "")
        if spicy_take:
            y_pos += 80
            font_spicy = self._get_font("body", 26)
            wrapped = self._wrap_text(f'💭 "{spicy_take}"', font_spicy, width - 100)
            for line in wrapped:
                self._draw_centered_text(
                    draw, line, width, y_pos,
                    font_spicy, self.brand.colors.text_secondary
                )
                y_pos += 35

        # Brand footer
        self._draw_brand_footer(draw, width, height)

        return self._image_to_bytes(img)

    def _create_gradient_background(
        self,
        width: int,
        height: int,
    ) -> Image.Image:
        """Create a gradient background image."""
        img = Image.new('RGB', (width, height))

        # Create vertical gradient
        top_color = self.brand.colors.to_rgb(self.brand.colors.background)
        bottom_color = self.brand.colors.to_rgb(self.brand.colors.background_alt)

        for y in range(height):
            ratio = y / height
            r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
            g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
            b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)

            for x in range(width):
                img.putpixel((x, y), (r, g, b))

        return img

    def _add_decorative_elements(self, img: Image.Image, draw: ImageDraw.Draw):
        """Add decorative shapes to the background."""
        width, height = img.size

        # Add subtle circles
        accent_rgba = self.brand.colors.to_rgba(self.brand.colors.primary, 0.1)

        # Top right circle
        draw.ellipse(
            [width - 200, -100, width + 100, 200],
            fill=None,
            outline=self.brand.colors.primary,
            width=2
        )

        # Bottom left circle
        draw.ellipse(
            [-100, height - 200, 200, height + 100],
            fill=None,
            outline=self.brand.colors.secondary,
            width=2
        )

    def _draw_brand_header(
        self,
        draw: ImageDraw.Draw,
        width: int,
        y: int,
    ) -> int:
        """Draw brand header with logo text."""
        font = self._get_font("heading", 32)
        self._draw_centered_text(
            draw, self.brand.name.upper(), width, y,
            font, self.brand.colors.primary
        )
        return y + 50

    def _draw_brand_footer(
        self,
        draw: ImageDraw.Draw,
        width: int,
        height: int,
    ):
        """Draw brand footer with handle."""
        font = self._get_font("body", 24)
        y = height - 60
        self._draw_centered_text(
            draw, f"Follow {self.brand.handle} for more 🔥", width, y,
            font, self.brand.colors.text_secondary
        )

    def _draw_vibe_meter(
        self,
        draw: ImageDraw.Draw,
        width: int,
        y: int,
        positive_pct: float,
        negative_pct: float,
        neutral_pct: float,
    ) -> int:
        """Draw a horizontal vibe meter bar."""
        bar_margin = 80
        bar_width = width - (bar_margin * 2)
        bar_height = 40
        bar_x = bar_margin

        # Background bar
        draw.rounded_rectangle(
            [bar_x, y, bar_x + bar_width, y + bar_height],
            radius=20,
            fill=self.brand.colors.card_bg
        )

        # Calculate segment widths
        pos_width = int((positive_pct / 100) * bar_width)
        neg_width = int((negative_pct / 100) * bar_width)
        neu_width = bar_width - pos_width - neg_width

        # Draw segments
        x = bar_x
        if pos_width > 0:
            draw.rounded_rectangle(
                [x, y, x + pos_width, y + bar_height],
                radius=20,
                fill=self.brand.colors.positive
            )
            x += pos_width

        if neu_width > 0:
            draw.rectangle(
                [x, y, x + neu_width, y + bar_height],
                fill=self.brand.colors.neutral
            )
            x += neu_width

        if neg_width > 0:
            draw.rounded_rectangle(
                [x, y, x + neg_width, y + bar_height],
                radius=20,
                fill=self.brand.colors.negative
            )

        return y + bar_height

    def _draw_stat_row(
        self,
        draw: ImageDraw.Draw,
        emoji: str,
        label: str,
        pct: float,
        color: str,
        width: int,
        y: int,
    ) -> int:
        """Draw a statistics row."""
        font = self._get_font("body", 32)

        # Centered layout
        text = f"{emoji} {label}: {pct:.1f}%"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2

        draw.text((x, y), text, font=font, fill=color)

        return y + 50

    def _draw_comment_card(
        self,
        img: Image.Image,
        draw: ImageDraw.Draw,
        x: int,
        y: int,
        width: int,
        username: str,
        text: str,
        number: int,
        theme: str,
    ) -> int:
        """Draw a comment card and return the new y position."""
        padding = 25
        corner_radius = 20

        # Calculate card height based on text
        font_user = self._get_font("body", 22)
        font_text = self._get_font("body", 26)

        wrapped_text = self._wrap_text(text, font_text, width - (padding * 2) - 20)
        text_height = len(wrapped_text) * 35

        card_height = padding + 30 + text_height + padding + 20

        # Theme colors
        if theme == "positive":
            border_color = self.brand.colors.positive
            number_bg = self.brand.colors.positive
        else:
            border_color = self.brand.colors.negative
            number_bg = self.brand.colors.negative

        # Card background
        draw.rounded_rectangle(
            [x, y, x + width, y + card_height],
            radius=corner_radius,
            fill=self.brand.colors.card_bg,
            outline=border_color,
            width=2
        )

        # Number badge
        badge_size = 35
        draw.ellipse(
            [x + padding, y + padding, x + padding + badge_size, y + padding + badge_size],
            fill=number_bg
        )
        font_num = self._get_font("body", 20)
        num_bbox = draw.textbbox((0, 0), str(number), font=font_num)
        num_x = x + padding + (badge_size - (num_bbox[2] - num_bbox[0])) // 2
        num_y = y + padding + (badge_size - (num_bbox[3] - num_bbox[1])) // 2
        draw.text((num_x, num_y), str(number), font=font_num, fill=self.brand.colors.text)

        # Username
        user_x = x + padding + badge_size + 15
        draw.text(
            (user_x, y + padding + 5),
            f"@{username}",
            font=font_user,
            fill=self.brand.colors.text_secondary
        )

        # Comment text
        text_y = y + padding + 45
        for line in wrapped_text:
            draw.text(
                (x + padding + 10, text_y),
                line,
                font=font_text,
                fill=self.brand.colors.text
            )
            text_y += 35

        return y + card_height

    def _draw_centered_text(
        self,
        draw: ImageDraw.Draw,
        text: str,
        width: int,
        y: int,
        font: ImageFont.FreeTypeFont,
        color: str,
    ):
        """Draw centered text."""
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        draw.text((x, y), text, font=font, fill=color)

    def _wrap_text(
        self,
        text: str,
        font: ImageFont.FreeTypeFont,
        max_width: int,
    ) -> List[str]:
        """Wrap text to fit within max_width."""
        words = text.split()
        lines = []
        current_line = []

        # Create a temporary image for measuring
        temp_img = Image.new('RGB', (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)

        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = temp_draw.textbbox((0, 0), test_line, font=font)

            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        return lines

    def _get_font(self, style: str, size: int) -> ImageFont.FreeTypeFont:
        """Get a font, using cache."""
        cache_key = f"{style}_{size}"

        if cache_key not in self.fonts_cache:
            # Try to load custom font, fall back to default
            try:
                font_name = getattr(self.brand.fonts, style, "Arial")
                self.fonts_cache[cache_key] = ImageFont.truetype(font_name, size)
            except (OSError, IOError):
                # Fall back to default font
                try:
                    self.fonts_cache[cache_key] = ImageFont.truetype("arial.ttf", size)
                except (OSError, IOError):
                    self.fonts_cache[cache_key] = ImageFont.load_default()

        return self.fonts_cache[cache_key]

    def _image_to_bytes(self, img: Image.Image) -> bytes:
        """Convert PIL Image to PNG bytes."""
        buffer = io.BytesIO()
        img.save(buffer, format='PNG', optimize=True)
        buffer.seek(0)
        return buffer.getvalue()
