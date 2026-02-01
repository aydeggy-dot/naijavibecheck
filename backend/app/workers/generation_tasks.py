"""Celery tasks for content generation."""

import asyncio
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.workers.celery_app import celery_app
from app.database import SyncSessionLocal, AsyncSessionLocal
from app.models import PostAnalysis, GeneratedContent, Post

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def generate_content_for_analysis(self, analysis_id: str, content_type: str = "auto"):
    """
    Generate visual content for an analyzed post.

    This task:
    1. Gets the analysis and related data
    2. Uses the image generator to create visuals
    3. Creates captions and hashtags
    4. Stores generated content with 'pending_review' status
    """
    logger.info(f"Generating content for analysis: {analysis_id}")

    from app.services.generator.content_pipeline import generate_content_for_post

    async def _generate():
        async with AsyncSessionLocal() as db:
            result = await generate_content_for_post(
                db,
                UUID(analysis_id),
                content_type=content_type,
            )
            await db.commit()
            return result

    try:
        result = asyncio.run(_generate())

        if result:
            logger.info(f"Generated content {result.id} for analysis {analysis_id}")
            return {
                "status": "success",
                "content_id": str(result.id),
                "content_type": result.content_type,
                "slides": len(result.media_urls) if result.media_urls else 0,
            }
        else:
            logger.warning(f"Failed to generate content for analysis {analysis_id}")
            return {"status": "failed", "analysis_id": analysis_id}

    except Exception as e:
        logger.error(f"Error generating content for {analysis_id}: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True)
def process_content_queue(self, limit: int = 5):
    """
    Process the content generation queue.

    Finds analyzed posts without content and generates it.
    """
    logger.info("Processing content generation queue")

    try:
        db = SyncSessionLocal()

        # Find analyzed posts without generated content
        analyzed_posts = (
            db.query(Post)
            .options(selectinload(Post.analysis))
            .filter(Post.is_analyzed == True)
            .filter(Post.is_processed == False)
            .order_by(Post.viral_score.desc())
            .limit(limit)
            .all()
        )

        logger.info(f"Found {len(analyzed_posts)} posts needing content generation")

        queued = 0
        for post in analyzed_posts:
            if post.analysis:
                generate_content_for_analysis.delay(str(post.analysis.id))
                queued += 1

        db.close()

        return {"status": "queued", "count": queued}

    except Exception as e:
        logger.error(f"Error processing content queue: {e}")
        raise


@celery_app.task(bind=True)
def regenerate_content(self, content_id: str, content_type: str = None):
    """
    Regenerate content for an existing GeneratedContent record.

    Useful for trying different styles or fixing issues.
    """
    logger.info(f"Regenerating content: {content_id}")

    try:
        db = SyncSessionLocal()

        content = (
            db.query(GeneratedContent)
            .filter(GeneratedContent.id == content_id)
            .first()
        )

        if not content:
            logger.warning(f"Content {content_id} not found")
            db.close()
            return {"status": "not_found"}

        analysis_id = str(content.post_analysis_id)
        use_type = content_type or content.content_type

        db.close()

        # Generate new content
        return generate_content_for_analysis(analysis_id, use_type)

    except Exception as e:
        logger.error(f"Error regenerating content {content_id}: {e}")
        raise


@celery_app.task(bind=True)
def generate_carousel(self, analysis_id: str):
    """Generate a carousel post specifically."""
    return generate_content_for_analysis(analysis_id, content_type="carousel")


@celery_app.task(bind=True)
def generate_single_image(self, analysis_id: str):
    """Generate a single image post."""
    return generate_content_for_analysis(analysis_id, content_type="image")


@celery_app.task(bind=True)
def cleanup_old_media(self, days_old: int = 30):
    """
    Clean up old generated media files.

    Removes media for rejected content older than specified days.
    """
    logger.info(f"Cleaning up media older than {days_old} days")

    from datetime import datetime, timedelta
    from pathlib import Path
    import shutil

    try:
        db = SyncSessionLocal()
        cutoff = datetime.utcnow() - timedelta(days=days_old)

        # Find old rejected content
        old_content = (
            db.query(GeneratedContent)
            .filter(GeneratedContent.status == "rejected")
            .filter(GeneratedContent.created_at < cutoff)
            .all()
        )

        removed = 0
        for content in old_content:
            if content.media_urls:
                for url in content.media_urls:
                    try:
                        path = Path(url)
                        if path.exists():
                            if path.is_dir():
                                shutil.rmtree(path)
                            else:
                                path.unlink()
                            removed += 1
                    except Exception as e:
                        logger.warning(f"Could not remove {url}: {e}")

            # Clear media URLs
            content.media_urls = None
            content.thumbnail_url = None

        db.commit()
        db.close()

        logger.info(f"Cleaned up {removed} media files")
        return {"status": "success", "removed": removed}

    except Exception as e:
        logger.error(f"Error cleaning up media: {e}")
        raise
