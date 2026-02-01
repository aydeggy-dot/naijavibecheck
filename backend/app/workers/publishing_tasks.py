"""Celery tasks for Instagram publishing."""

import asyncio
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.workers.celery_app import celery_app
from app.database import SyncSessionLocal, AsyncSessionLocal
from app.models import GeneratedContent, OurEngagement
from app.config import settings

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def publish_scheduled_content(self):
    """
    Check for content scheduled to be published and publish it.

    Runs every 5 minutes via Celery beat.
    """
    logger.info("Checking for scheduled content to publish")

    from app.services.publisher.scheduler import ContentScheduler

    async def _process():
        async with AsyncSessionLocal() as db:
            scheduler = ContentScheduler()
            use_mock = settings.environment == "development"
            result = await scheduler.process_publishing_queue(db, use_mock=use_mock)
            await db.commit()
            return result

    try:
        result = asyncio.run(_process())
        logger.info(f"Publishing queue result: {result}")
        return result

    except Exception as e:
        logger.error(f"Error processing publishing queue: {e}")
        raise


@celery_app.task(bind=True, max_retries=3)
def publish_content_now(self, content_id: str):
    """
    Immediately publish a specific piece of content.

    Args:
        content_id: GeneratedContent UUID
    """
    logger.info(f"Publishing content: {content_id}")

    from app.services.publisher.scheduler import ContentScheduler

    async def _publish():
        async with AsyncSessionLocal() as db:
            scheduler = ContentScheduler()
            use_mock = settings.environment == "development"
            result = await scheduler.publish_content(
                db, UUID(content_id), use_mock=use_mock
            )
            await db.commit()
            return result

    try:
        result = asyncio.run(_publish())

        if result["status"] == "success":
            logger.info(f"Published content {content_id}")
            # Schedule engagement tracking
            track_content_engagement.apply_async(
                args=[content_id],
                countdown=3600,  # Check after 1 hour
            )
        else:
            logger.error(f"Failed to publish {content_id}: {result.get('message')}")

        return result

    except Exception as e:
        logger.error(f"Error publishing content {content_id}: {e}")
        raise self.retry(exc=e, countdown=300)


@celery_app.task(bind=True)
def track_engagement(self):
    """
    Track engagement metrics for all published content.

    Runs daily to update engagement data.
    """
    logger.info("Tracking engagement for published content")

    from app.services.publisher.instagram_publisher import get_publisher

    try:
        db = SyncSessionLocal()

        # Get published content with Instagram IDs
        published = (
            db.query(GeneratedContent)
            .filter(GeneratedContent.status == "published")
            .filter(GeneratedContent.instagram_post_id.isnot(None))
            .all()
        )

        logger.info(f"Tracking engagement for {len(published)} posts")

        use_mock = settings.environment == "development"
        tracked = 0

        for content in published:
            try:
                # Get insights from Instagram
                publisher = get_publisher(mock=use_mock)

                async def _get_insights():
                    await publisher.initialize()
                    return await publisher.get_media_insights(content.instagram_post_id)

                insights = asyncio.run(_get_insights())

                if insights:
                    # Create engagement record
                    engagement = OurEngagement(
                        generated_content_id=content.id,
                        like_count=insights.get("like_count"),
                        comment_count=insights.get("comment_count"),
                    )
                    db.add(engagement)
                    tracked += 1

            except Exception as e:
                logger.warning(f"Could not track engagement for {content.id}: {e}")

        db.commit()
        db.close()

        logger.info(f"Tracked engagement for {tracked} posts")
        return {"status": "success", "tracked": tracked}

    except Exception as e:
        logger.error(f"Error tracking engagement: {e}")
        raise


@celery_app.task(bind=True, max_retries=3)
def track_content_engagement(self, content_id: str):
    """
    Track engagement for a specific piece of content.

    Called after publishing to monitor performance.
    """
    logger.info(f"Tracking engagement for content: {content_id}")

    from app.services.publisher.instagram_publisher import get_publisher

    try:
        db = SyncSessionLocal()

        content = (
            db.query(GeneratedContent)
            .filter(GeneratedContent.id == content_id)
            .first()
        )

        if not content or not content.instagram_post_id:
            logger.warning(f"Content {content_id} not found or not published")
            db.close()
            return {"status": "not_found"}

        use_mock = settings.environment == "development"
        publisher = get_publisher(mock=use_mock)

        async def _get_insights():
            await publisher.initialize()
            return await publisher.get_media_insights(content.instagram_post_id)

        insights = asyncio.run(_get_insights())

        if insights:
            engagement = OurEngagement(
                generated_content_id=content.id,
                like_count=insights.get("like_count"),
                comment_count=insights.get("comment_count"),
            )
            db.add(engagement)
            db.commit()

            logger.info(f"Tracked engagement for {content_id}: {insights}")

            # Calculate engagement rate if we have follower data
            # and update content performance for learning

        db.close()
        return {"status": "success", "insights": insights}

    except Exception as e:
        logger.error(f"Error tracking engagement for {content_id}: {e}")
        raise self.retry(exc=e, countdown=600)


@celery_app.task(bind=True)
def schedule_optimal_time(self, content_id: str):
    """
    Schedule content for optimal posting time.

    Args:
        content_id: GeneratedContent UUID
    """
    logger.info(f"Scheduling content for optimal time: {content_id}")

    from app.services.publisher.scheduler import ContentScheduler

    async def _schedule():
        async with AsyncSessionLocal() as db:
            scheduler = ContentScheduler()
            result = await scheduler.schedule_content(db, UUID(content_id))
            await db.commit()
            return result

    try:
        result = asyncio.run(_schedule())
        logger.info(f"Scheduled {content_id}: {result}")
        return result

    except Exception as e:
        logger.error(f"Error scheduling content {content_id}: {e}")
        raise


@celery_app.task(bind=True)
def auto_approve_high_score_content(self, min_viral_score: float = 80.0):
    """
    Automatically approve content from highly viral posts.

    Only for fully autonomous mode.
    """
    logger.info(f"Auto-approving content from posts with viral score >= {min_viral_score}")

    try:
        db = SyncSessionLocal()

        # Find pending content from high-score posts
        pending_content = (
            db.query(GeneratedContent)
            .join(GeneratedContent.post_analysis)
            .join("post")
            .filter(GeneratedContent.status == "pending_review")
            .filter(GeneratedContent.post_analysis.has(
                post=lambda p: p.viral_score >= min_viral_score
            ))
            .all()
        )

        approved = 0
        for content in pending_content:
            content.status = "approved"
            approved += 1

        db.commit()
        db.close()

        logger.info(f"Auto-approved {approved} pieces of content")
        return {"status": "success", "approved": approved}

    except Exception as e:
        logger.error(f"Error in auto-approve: {e}")
        raise


@celery_app.task(bind=True)
def update_account_stats(self):
    """
    Update our Instagram account statistics.

    Tracks follower growth over time.
    """
    logger.info("Updating account statistics")

    from app.services.publisher.instagram_publisher import get_publisher
    from app.models import Settings

    try:
        use_mock = settings.environment == "development"
        publisher = get_publisher(mock=use_mock)

        async def _get_stats():
            await publisher.initialize()
            return await publisher.get_account_insights()

        stats = asyncio.run(_get_stats())

        if stats:
            db = SyncSessionLocal()

            # Store in settings
            existing = db.query(Settings).filter(Settings.key == "account_stats").first()
            if existing:
                existing.value = {
                    **stats,
                    "updated_at": datetime.utcnow().isoformat(),
                }
            else:
                setting = Settings(
                    key="account_stats",
                    value={
                        **stats,
                        "updated_at": datetime.utcnow().isoformat(),
                    },
                )
                db.add(setting)

            db.commit()
            db.close()

            logger.info(f"Updated account stats: {stats}")
            return {"status": "success", "stats": stats}

        return {"status": "failed", "message": "Could not get stats"}

    except Exception as e:
        logger.error(f"Error updating account stats: {e}")
        raise
