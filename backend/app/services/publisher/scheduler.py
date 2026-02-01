"""Content scheduling service."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import GeneratedContent, Post, PostAnalysis
from app.services.publisher.optimal_time import OptimalTimeCalculator
from app.services.publisher.instagram_publisher import get_publisher

logger = logging.getLogger(__name__)


class ContentScheduler:
    """
    Manage content scheduling and publishing workflow.

    Features:
    - Schedule content for optimal times
    - Manage approval workflow
    - Handle publishing queue
    - Track publishing status
    """

    def __init__(self):
        self.time_calculator = OptimalTimeCalculator()

    async def schedule_content(
        self,
        db: AsyncSession,
        content_id: UUID,
        scheduled_time: datetime = None,
        auto_approve: bool = False,
    ) -> Dict[str, Any]:
        """
        Schedule content for publishing.

        Args:
            db: Database session
            content_id: GeneratedContent UUID
            scheduled_time: When to publish (None = auto-calculate)
            auto_approve: Automatically approve for publishing

        Returns:
            Scheduling result dict
        """
        content = await db.get(GeneratedContent, content_id)
        if not content:
            return {"status": "error", "message": "Content not found"}

        if content.status == "published":
            return {"status": "error", "message": "Content already published"}

        # Calculate optimal time if not provided
        if scheduled_time is None:
            scheduled_time = await self.time_calculator.get_optimal_time(
                db,
                content_type=content.content_type,
            )

        content.scheduled_for = scheduled_time

        if auto_approve:
            content.status = "approved"
        elif content.status == "draft":
            content.status = "pending_review"

        await db.commit()

        logger.info(f"Scheduled content {content_id} for {scheduled_time}")

        return {
            "status": "success",
            "content_id": str(content_id),
            "scheduled_for": scheduled_time.isoformat(),
            "content_status": content.status,
        }

    async def get_scheduled_content(
        self,
        db: AsyncSession,
        status: str = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Get scheduled content.

        Args:
            db: Database session
            status: Filter by status
            limit: Maximum results

        Returns:
            List of scheduled content
        """
        query = (
            select(GeneratedContent)
            .where(GeneratedContent.scheduled_for.isnot(None))
            .order_by(GeneratedContent.scheduled_for)
            .limit(limit)
        )

        if status:
            query = query.where(GeneratedContent.status == status)

        result = await db.execute(query)
        content_list = result.scalars().all()

        return [
            {
                "id": str(c.id),
                "title": c.title,
                "content_type": c.content_type,
                "status": c.status,
                "scheduled_for": c.scheduled_for.isoformat() if c.scheduled_for else None,
                "created_at": c.created_at.isoformat(),
            }
            for c in content_list
        ]

    async def get_ready_to_publish(
        self,
        db: AsyncSession,
    ) -> List[GeneratedContent]:
        """
        Get content that is approved and ready to publish now.

        Returns content where:
        - Status is 'approved'
        - Scheduled time has passed (or is within 5 minutes)
        """
        cutoff = datetime.utcnow() + timedelta(minutes=5)

        result = await db.execute(
            select(GeneratedContent)
            .where(GeneratedContent.status == "approved")
            .where(GeneratedContent.scheduled_for <= cutoff)
            .order_by(GeneratedContent.scheduled_for)
        )

        return result.scalars().all()

    async def publish_content(
        self,
        db: AsyncSession,
        content_id: UUID,
        use_mock: bool = False,
    ) -> Dict[str, Any]:
        """
        Publish content to Instagram.

        Args:
            db: Database session
            content_id: GeneratedContent UUID
            use_mock: Use mock publisher

        Returns:
            Publishing result dict
        """
        content = await db.get(GeneratedContent, content_id)
        if not content:
            return {"status": "error", "message": "Content not found"}

        if content.status == "published":
            return {"status": "error", "message": "Already published"}

        if content.status != "approved":
            return {"status": "error", "message": "Content not approved"}

        if not content.media_urls:
            return {"status": "error", "message": "No media files"}

        publisher = get_publisher(mock=use_mock)

        try:
            # Publish based on content type
            if content.content_type == "carousel" and len(content.media_urls) > 1:
                media_id = await publisher.publish_carousel(
                    image_paths=content.media_urls,
                    caption=content.caption or "",
                )
            else:
                media_id = await publisher.publish_image(
                    image_path=content.media_urls[0],
                    caption=content.caption or "",
                )

            if media_id:
                content.status = "published"
                content.published_at = datetime.utcnow()
                content.instagram_post_id = media_id

                await db.commit()

                logger.info(f"Published content {content_id} as {media_id}")
                return {
                    "status": "success",
                    "content_id": str(content_id),
                    "instagram_id": media_id,
                    "published_at": content.published_at.isoformat(),
                }
            else:
                return {"status": "error", "message": "Publishing failed"}

        except Exception as e:
            logger.error(f"Error publishing content {content_id}: {e}")
            return {"status": "error", "message": str(e)}

    async def process_publishing_queue(
        self,
        db: AsyncSession,
        use_mock: bool = False,
    ) -> Dict[str, Any]:
        """
        Process all content ready for publishing.

        Returns:
            Summary of publishing results
        """
        ready_content = await self.get_ready_to_publish(db)

        if not ready_content:
            return {"status": "empty", "published": 0}

        published = 0
        failed = 0

        for content in ready_content:
            result = await self.publish_content(db, content.id, use_mock=use_mock)
            if result["status"] == "success":
                published += 1
            else:
                failed += 1
                logger.error(f"Failed to publish {content.id}: {result.get('message')}")

        return {
            "status": "completed",
            "published": published,
            "failed": failed,
        }

    async def approve_content(
        self,
        db: AsyncSession,
        content_id: UUID,
        schedule_now: bool = True,
    ) -> Dict[str, Any]:
        """
        Approve content for publishing.

        Args:
            db: Database session
            content_id: GeneratedContent UUID
            schedule_now: Schedule for optimal time

        Returns:
            Approval result
        """
        content = await db.get(GeneratedContent, content_id)
        if not content:
            return {"status": "error", "message": "Content not found"}

        if content.status == "published":
            return {"status": "error", "message": "Already published"}

        content.status = "approved"

        if schedule_now and not content.scheduled_for:
            content.scheduled_for = await self.time_calculator.get_optimal_time(
                db, content_type=content.content_type
            )

        await db.commit()

        return {
            "status": "success",
            "content_id": str(content_id),
            "scheduled_for": content.scheduled_for.isoformat() if content.scheduled_for else None,
        }

    async def reject_content(
        self,
        db: AsyncSession,
        content_id: UUID,
        reason: str = None,
    ) -> Dict[str, Any]:
        """
        Reject content.

        Args:
            db: Database session
            content_id: GeneratedContent UUID
            reason: Rejection reason

        Returns:
            Rejection result
        """
        content = await db.get(GeneratedContent, content_id)
        if not content:
            return {"status": "error", "message": "Content not found"}

        if content.status == "published":
            return {"status": "error", "message": "Cannot reject published content"}

        content.status = "rejected"
        if reason:
            metadata = content.generation_metadata or {}
            metadata["rejection_reason"] = reason
            content.generation_metadata = metadata

        await db.commit()

        return {
            "status": "success",
            "content_id": str(content_id),
        }

    async def reschedule_content(
        self,
        db: AsyncSession,
        content_id: UUID,
        new_time: datetime,
    ) -> Dict[str, Any]:
        """
        Reschedule content to a different time.

        Args:
            db: Database session
            content_id: GeneratedContent UUID
            new_time: New scheduled time

        Returns:
            Rescheduling result
        """
        content = await db.get(GeneratedContent, content_id)
        if not content:
            return {"status": "error", "message": "Content not found"}

        if content.status == "published":
            return {"status": "error", "message": "Cannot reschedule published content"}

        content.scheduled_for = new_time

        await db.commit()

        return {
            "status": "success",
            "content_id": str(content_id),
            "scheduled_for": new_time.isoformat(),
        }

    async def get_publishing_stats(
        self,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Get publishing statistics.

        Returns:
            Stats dict
        """
        from sqlalchemy import func

        # Count by status
        status_counts = await db.execute(
            select(GeneratedContent.status, func.count())
            .group_by(GeneratedContent.status)
        )

        # Upcoming scheduled
        upcoming = await db.scalar(
            select(func.count())
            .select_from(GeneratedContent)
            .where(GeneratedContent.status == "approved")
            .where(GeneratedContent.scheduled_for > datetime.utcnow())
        )

        # Published today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0)
        published_today = await db.scalar(
            select(func.count())
            .select_from(GeneratedContent)
            .where(GeneratedContent.status == "published")
            .where(GeneratedContent.published_at >= today_start)
        )

        return {
            "by_status": {row[0]: row[1] for row in status_counts},
            "upcoming_scheduled": upcoming,
            "published_today": published_today,
        }
