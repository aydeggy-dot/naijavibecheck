"""Content generation pipeline."""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import PostAnalysis, Comment, GeneratedContent
from app.services.generator.image_generator import ImageGenerator
from app.services.generator.carousel_generator import CarouselGenerator
from app.services.generator.caption_generator import CaptionGenerator
from app.services.generator.brand_config import get_brand_config
from app.config import settings

logger = logging.getLogger(__name__)


class ContentPipeline:
    """
    Full content generation pipeline.

    Pipeline stages:
    1. Fetch analysis data
    2. Select content type (carousel, single image)
    3. Generate images
    4. Generate caption
    5. Save media files
    6. Create GeneratedContent record
    """

    def __init__(self):
        self.brand = get_brand_config()
        self.image_generator = ImageGenerator(self.brand)
        self.carousel_generator = CarouselGenerator(self.brand)
        self.caption_generator = CaptionGenerator(self.brand)
        self.media_dir = Path(settings.generated_media_dir)
        self.media_dir.mkdir(parents=True, exist_ok=True)

    async def generate_content(
        self,
        db: AsyncSession,
        analysis_id: UUID,
        content_type: str = "auto",
    ) -> Optional[GeneratedContent]:
        """
        Generate content for an analyzed post.

        Args:
            db: Database session
            analysis_id: PostAnalysis UUID
            content_type: "carousel", "image", or "auto"

        Returns:
            GeneratedContent object or None
        """
        logger.info(f"Starting content generation for analysis {analysis_id}")

        # Stage 1: Fetch analysis data
        analysis = await self._fetch_analysis(db, analysis_id)
        if not analysis:
            logger.error(f"Analysis {analysis_id} not found")
            return None

        post = analysis.post
        celebrity = post.celebrity
        celebrity_name = celebrity.full_name or celebrity.instagram_username

        # Prepare stats
        stats = {
            "total": analysis.total_comments_analyzed,
            "positive_count": analysis.positive_count,
            "negative_count": analysis.negative_count,
            "neutral_count": analysis.neutral_count,
            "positive_pct": analysis.positive_percentage,
            "negative_pct": analysis.negative_percentage,
            "neutral_pct": analysis.neutral_percentage,
            "controversy_score": analysis.controversy_score or 0,
        }

        ai_insights = analysis.ai_insights or {}

        # Fetch top comments
        top_positive = await self._fetch_top_comments(
            db, analysis.top_positive_comment_ids
        )
        top_negative = await self._fetch_top_comments(
            db, analysis.top_negative_comment_ids
        )

        # Stage 2: Select content type
        if content_type == "auto":
            content_type = self._select_content_type(stats, ai_insights)

        # Stage 3: Generate images
        if content_type == "carousel":
            carousel_type = self.carousel_generator.select_carousel_type(stats, ai_insights)

            if carousel_type == "controversy":
                images = self.carousel_generator.generate_controversy_carousel(
                    celebrity_name, stats, top_positive, top_negative, ai_insights
                )
            elif carousel_type == "minimal":
                images = self.carousel_generator.generate_minimal_carousel(
                    celebrity_name, stats, ai_insights
                )
            else:
                images = self.carousel_generator.generate_standard_carousel(
                    celebrity_name, stats, top_positive, top_negative, ai_insights
                )
        else:
            # Single image
            headline = ai_insights.get("headline", "The vibes are in! 🔥")
            image = self.image_generator.generate_stats_card(
                celebrity_name, stats, headline
            )
            images = [image]

        # Stage 4: Generate caption
        caption_data = await self.caption_generator.generate_caption(
            celebrity_name, stats, ai_insights, content_type
        )

        full_caption = self.caption_generator.build_full_caption(
            caption_data["caption"],
            caption_data["call_to_action"],
            caption_data["hashtags"],
        )

        # Stage 5: Save media files
        content_id = uuid4()
        media_urls = await self._save_media_files(content_id, images)

        # Stage 6: Create GeneratedContent record
        generated_content = GeneratedContent(
            id=content_id,
            post_analysis_id=analysis_id,
            content_type=content_type,
            title=ai_insights.get("headline", f"{celebrity_name} Vibe Check"),
            caption=full_caption,
            hashtags=caption_data["hashtags"],
            media_urls=media_urls,
            thumbnail_url=media_urls[0] if media_urls else None,
            status="pending_review",
            generation_metadata={
                "celebrity_name": celebrity_name,
                "stats": stats,
                "ai_insights": ai_insights,
                "carousel_type": carousel_type if content_type == "carousel" else None,
                "slides_count": len(images),
            },
        )

        db.add(generated_content)

        # Mark post as processed
        post.is_processed = True

        await db.flush()

        logger.info(
            f"Generated {content_type} content ({len(images)} slides) "
            f"for {celebrity_name}: {content_id}"
        )

        return generated_content

    async def _fetch_analysis(
        self,
        db: AsyncSession,
        analysis_id: UUID,
    ) -> Optional[PostAnalysis]:
        """Fetch analysis with related data."""
        result = await db.execute(
            select(PostAnalysis)
            .options(
                selectinload(PostAnalysis.post).selectinload("celebrity"),
            )
            .where(PostAnalysis.id == analysis_id)
        )
        return result.scalar_one_or_none()

    async def _fetch_top_comments(
        self,
        db: AsyncSession,
        comment_ids: Optional[List[UUID]],
    ) -> List[Dict[str, Any]]:
        """Fetch top comments by IDs."""
        if not comment_ids:
            return []

        result = await db.execute(
            select(Comment).where(Comment.id.in_(comment_ids))
        )
        comments = result.scalars().all()

        return [
            {
                "id": str(c.id),
                "username_anonymized": c.username_anonymized,
                "text": c.text,
                "like_count": c.like_count,
            }
            for c in comments
        ]

    def _select_content_type(
        self,
        stats: Dict[str, Any],
        ai_insights: Dict[str, Any],
    ) -> str:
        """Automatically select content type based on data."""
        total_comments = stats.get("total", 0)

        # If we have enough data, prefer carousel
        if total_comments >= 100:
            return "carousel"

        # Otherwise single image
        return "image"

    async def _save_media_files(
        self,
        content_id: UUID,
        images: List[bytes],
    ) -> List[str]:
        """
        Save image files and return URLs/paths.

        In production, this would upload to S3/DigitalOcean Spaces.
        For now, saves locally.
        """
        media_urls = []
        content_dir = self.media_dir / str(content_id)
        content_dir.mkdir(parents=True, exist_ok=True)

        for i, image_bytes in enumerate(images):
            filename = f"slide_{i + 1}.png"
            filepath = content_dir / filename
            filepath.write_bytes(image_bytes)

            # In production, this would be the CDN URL
            media_urls.append(str(filepath))

        return media_urls


async def generate_content_for_post(
    db: AsyncSession,
    analysis_id: UUID,
    content_type: str = "auto",
) -> Optional[GeneratedContent]:
    """
    Convenience function to generate content.

    Args:
        db: Database session
        analysis_id: PostAnalysis UUID
        content_type: Content type or "auto"

    Returns:
        GeneratedContent or None
    """
    pipeline = ContentPipeline()
    return await pipeline.generate_content(db, analysis_id, content_type)
