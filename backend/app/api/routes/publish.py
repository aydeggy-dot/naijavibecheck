"""Publishing API endpoints."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models import GeneratedContent
from app.services.publisher.scheduler import ContentScheduler
from app.services.publisher.optimal_time import OptimalTimeCalculator
from app.config import settings

router = APIRouter()


class ScheduleRequest(BaseModel):
    """Request to schedule content."""
    scheduled_time: Optional[datetime] = None
    auto_approve: bool = False


class RescheduleRequest(BaseModel):
    """Request to reschedule content."""
    new_time: datetime


class ApproveRequest(BaseModel):
    """Request to approve content."""
    schedule_now: bool = True


class RejectRequest(BaseModel):
    """Request to reject content."""
    reason: Optional[str] = None


@router.post("/content/{content_id}/schedule")
async def schedule_content(
    content_id: UUID,
    request: ScheduleRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Schedule content for publishing.

    If no time provided, calculates optimal time automatically.
    """
    scheduler = ContentScheduler()
    result = await scheduler.schedule_content(
        db,
        content_id,
        scheduled_time=request.scheduled_time,
        auto_approve=request.auto_approve,
    )

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.post("/content/{content_id}/reschedule")
async def reschedule_content(
    content_id: UUID,
    request: RescheduleRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Reschedule content to a different time.
    """
    scheduler = ContentScheduler()
    result = await scheduler.reschedule_content(
        db, content_id, request.new_time
    )

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.post("/content/{content_id}/approve")
async def approve_content(
    content_id: UUID,
    request: ApproveRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Approve content for publishing.
    """
    scheduler = ContentScheduler()
    result = await scheduler.approve_content(
        db, content_id, schedule_now=request.schedule_now
    )

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.post("/content/{content_id}/reject")
async def reject_content(
    content_id: UUID,
    request: RejectRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Reject content.
    """
    scheduler = ContentScheduler()
    result = await scheduler.reject_content(
        db, content_id, reason=request.reason
    )

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.post("/content/{content_id}/publish")
async def publish_content_now(
    content_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Immediately publish content (bypasses schedule).
    """
    # Verify content exists and is approved
    content = await db.get(GeneratedContent, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    if content.status == "published":
        raise HTTPException(status_code=400, detail="Already published")

    if content.status not in ["approved", "pending_review"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot publish content with status '{content.status}'"
        )

    # Auto-approve if pending
    if content.status == "pending_review":
        content.status = "approved"
        await db.commit()

    # Queue for immediate publishing
    from app.workers.publishing_tasks import publish_content_now as publish_task
    publish_task.delay(str(content_id))

    return {
        "status": "queued",
        "content_id": str(content_id),
        "message": "Publishing queued for immediate execution",
    }


@router.get("/scheduled")
async def get_scheduled_content(
    status: Optional[str] = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """
    Get scheduled content.
    """
    scheduler = ContentScheduler()
    content = await scheduler.get_scheduled_content(db, status=status, limit=limit)
    return {"items": content, "count": len(content)}


@router.get("/queue")
async def get_publishing_queue(db: AsyncSession = Depends(get_db)):
    """
    Get the current publishing queue.

    Returns content grouped by status.
    """
    from sqlalchemy import func

    # Get pending review
    pending_result = await db.execute(
        select(GeneratedContent)
        .where(GeneratedContent.status == "pending_review")
        .order_by(GeneratedContent.created_at.desc())
        .limit(20)
    )
    pending = pending_result.scalars().all()

    # Get approved (scheduled)
    approved_result = await db.execute(
        select(GeneratedContent)
        .where(GeneratedContent.status == "approved")
        .order_by(GeneratedContent.scheduled_for)
        .limit(20)
    )
    approved = approved_result.scalars().all()

    # Get recently published
    published_result = await db.execute(
        select(GeneratedContent)
        .where(GeneratedContent.status == "published")
        .order_by(GeneratedContent.published_at.desc())
        .limit(10)
    )
    published = published_result.scalars().all()

    def content_to_dict(c):
        return {
            "id": str(c.id),
            "title": c.title,
            "content_type": c.content_type,
            "status": c.status,
            "scheduled_for": c.scheduled_for.isoformat() if c.scheduled_for else None,
            "published_at": c.published_at.isoformat() if c.published_at else None,
            "created_at": c.created_at.isoformat(),
            "thumbnail_url": c.thumbnail_url,
        }

    return {
        "pending_review": [content_to_dict(c) for c in pending],
        "approved": [content_to_dict(c) for c in approved],
        "recently_published": [content_to_dict(c) for c in published],
        "counts": {
            "pending": len(pending),
            "approved": len(approved),
            "published": len(published),
        },
    }


@router.post("/queue/process")
async def process_publishing_queue(db: AsyncSession = Depends(get_db)):
    """
    Process the publishing queue.

    Publishes all approved content that is past its scheduled time.
    """
    scheduler = ContentScheduler()
    use_mock = settings.environment == "development"
    result = await scheduler.process_publishing_queue(db, use_mock=use_mock)
    return result


@router.get("/optimal-times")
async def get_optimal_times(
    count: int = 5,
    db: AsyncSession = Depends(get_db),
):
    """
    Get suggested optimal posting times.
    """
    calculator = OptimalTimeCalculator()
    suggestions = await calculator.get_schedule_suggestions(db, count=count)
    return {"suggestions": suggestions}


@router.get("/stats")
async def get_publishing_stats(db: AsyncSession = Depends(get_db)):
    """
    Get publishing statistics.
    """
    scheduler = ContentScheduler()
    stats = await scheduler.get_publishing_stats(db)
    return stats


@router.get("/account")
async def get_account_info(db: AsyncSession = Depends(get_db)):
    """
    Get Instagram account information.
    """
    from app.models import Settings

    result = await db.execute(
        select(Settings).where(Settings.key == "account_stats")
    )
    setting = result.scalar_one_or_none()

    if setting:
        return setting.value

    return {"message": "Account stats not available. Run update task first."}
