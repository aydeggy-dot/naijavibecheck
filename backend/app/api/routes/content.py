"""Content API endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models import GeneratedContent
from app.schemas.content import (
    ContentStatus,
    GeneratedContentResponse,
    GeneratedContentUpdate,
    ContentQueueResponse,
)

router = APIRouter()


@router.get("/queue", response_model=ContentQueueResponse)
async def get_content_queue(db: AsyncSession = Depends(get_db)):
    """Get the content queue grouped by status."""
    result = await db.execute(
        select(GeneratedContent).order_by(GeneratedContent.created_at.desc())
    )
    all_content = result.scalars().all()

    pending = []
    approved = []
    published = []
    rejected = []

    for content in all_content:
        item = GeneratedContentResponse(
            id=content.id,
            post_analysis_id=content.post_analysis_id,
            content_type=content.content_type,
            title=content.title,
            caption=content.caption,
            hashtags=content.hashtags,
            status=content.status,
            media_urls=content.media_urls,
            thumbnail_url=content.thumbnail_url,
            scheduled_for=content.scheduled_for,
            published_at=content.published_at,
            instagram_post_id=content.instagram_post_id,
            created_at=content.created_at,
            updated_at=content.updated_at,
        )

        if content.status == "pending_review":
            pending.append(item)
        elif content.status == "approved":
            approved.append(item)
        elif content.status == "published":
            published.append(item)
        elif content.status == "rejected":
            rejected.append(item)

    return ContentQueueResponse(
        pending=pending,
        approved=approved,
        published=published,
        rejected=rejected,
        total=len(all_content),
    )


@router.get("", response_model=list[GeneratedContentResponse])
async def list_content(
    status: Optional[ContentStatus] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List generated content with optional status filter."""
    query = select(GeneratedContent)

    if status:
        query = query.where(GeneratedContent.status == status.value)

    query = query.order_by(GeneratedContent.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    content_list = result.scalars().all()

    return [
        GeneratedContentResponse(
            id=content.id,
            post_analysis_id=content.post_analysis_id,
            content_type=content.content_type,
            title=content.title,
            caption=content.caption,
            hashtags=content.hashtags,
            status=content.status,
            media_urls=content.media_urls,
            thumbnail_url=content.thumbnail_url,
            scheduled_for=content.scheduled_for,
            published_at=content.published_at,
            instagram_post_id=content.instagram_post_id,
            created_at=content.created_at,
            updated_at=content.updated_at,
        )
        for content in content_list
    ]


@router.get("/{content_id}", response_model=GeneratedContentResponse)
async def get_content(
    content_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific piece of generated content."""
    result = await db.execute(
        select(GeneratedContent).where(GeneratedContent.id == content_id)
    )
    content = result.scalar_one_or_none()

    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    return GeneratedContentResponse(
        id=content.id,
        post_analysis_id=content.post_analysis_id,
        content_type=content.content_type,
        title=content.title,
        caption=content.caption,
        hashtags=content.hashtags,
        status=content.status,
        media_urls=content.media_urls,
        thumbnail_url=content.thumbnail_url,
        scheduled_for=content.scheduled_for,
        published_at=content.published_at,
        instagram_post_id=content.instagram_post_id,
        created_at=content.created_at,
        updated_at=content.updated_at,
    )


@router.patch("/{content_id}", response_model=GeneratedContentResponse)
async def update_content(
    content_id: UUID,
    data: GeneratedContentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update generated content (edit caption, approve, reject, etc.)."""
    result = await db.execute(
        select(GeneratedContent).where(GeneratedContent.id == content_id)
    )
    content = result.scalar_one_or_none()

    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "status" and value:
            setattr(content, field, value.value if hasattr(value, "value") else value)
        else:
            setattr(content, field, value)

    await db.commit()
    await db.refresh(content)

    return GeneratedContentResponse(
        id=content.id,
        post_analysis_id=content.post_analysis_id,
        content_type=content.content_type,
        title=content.title,
        caption=content.caption,
        hashtags=content.hashtags,
        status=content.status,
        media_urls=content.media_urls,
        thumbnail_url=content.thumbnail_url,
        scheduled_for=content.scheduled_for,
        published_at=content.published_at,
        instagram_post_id=content.instagram_post_id,
        created_at=content.created_at,
        updated_at=content.updated_at,
    )


@router.post("/{content_id}/approve", response_model=GeneratedContentResponse)
async def approve_content(
    content_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Approve content for publishing."""
    result = await db.execute(
        select(GeneratedContent).where(GeneratedContent.id == content_id)
    )
    content = result.scalar_one_or_none()

    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    if content.status not in ["draft", "pending_review"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve content with status '{content.status}'",
        )

    content.status = "approved"
    await db.commit()
    await db.refresh(content)

    return GeneratedContentResponse(
        id=content.id,
        post_analysis_id=content.post_analysis_id,
        content_type=content.content_type,
        title=content.title,
        caption=content.caption,
        hashtags=content.hashtags,
        status=content.status,
        media_urls=content.media_urls,
        thumbnail_url=content.thumbnail_url,
        scheduled_for=content.scheduled_for,
        published_at=content.published_at,
        instagram_post_id=content.instagram_post_id,
        created_at=content.created_at,
        updated_at=content.updated_at,
    )


@router.post("/{content_id}/reject", response_model=GeneratedContentResponse)
async def reject_content(
    content_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Reject content."""
    result = await db.execute(
        select(GeneratedContent).where(GeneratedContent.id == content_id)
    )
    content = result.scalar_one_or_none()

    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    if content.status == "published":
        raise HTTPException(
            status_code=400,
            detail="Cannot reject already published content",
        )

    content.status = "rejected"
    await db.commit()
    await db.refresh(content)

    return GeneratedContentResponse(
        id=content.id,
        post_analysis_id=content.post_analysis_id,
        content_type=content.content_type,
        title=content.title,
        caption=content.caption,
        hashtags=content.hashtags,
        status=content.status,
        media_urls=content.media_urls,
        thumbnail_url=content.thumbnail_url,
        scheduled_for=content.scheduled_for,
        published_at=content.published_at,
        instagram_post_id=content.instagram_post_id,
        created_at=content.created_at,
        updated_at=content.updated_at,
    )
