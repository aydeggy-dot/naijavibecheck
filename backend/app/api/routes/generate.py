"""Content generation API endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.models import PostAnalysis, GeneratedContent, Post
from app.services.generator import ContentPipeline, generate_content_for_post

router = APIRouter()


class GenerateRequest(BaseModel):
    """Request for content generation."""
    content_type: str = "auto"  # "auto", "carousel", "image"


class RegenerateRequest(BaseModel):
    """Request for content regeneration."""
    content_type: Optional[str] = None


@router.post("/analysis/{analysis_id}")
async def generate_content(
    analysis_id: UUID,
    request: GenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate content for an analyzed post.

    Args:
        analysis_id: PostAnalysis UUID
        request: Generation options
    """
    # Verify analysis exists
    result = await db.execute(
        select(PostAnalysis)
        .options(selectinload(PostAnalysis.post))
        .where(PostAnalysis.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Check if content already exists
    existing = await db.execute(
        select(GeneratedContent).where(GeneratedContent.post_analysis_id == analysis_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Content already generated. Use regenerate endpoint to create new content."
        )

    # Generate content
    content = await generate_content_for_post(
        db, analysis_id, content_type=request.content_type
    )

    if not content:
        raise HTTPException(status_code=500, detail="Content generation failed")

    return {
        "status": "success",
        "content_id": str(content.id),
        "content_type": content.content_type,
        "title": content.title,
        "slides_count": len(content.media_urls) if content.media_urls else 0,
        "status": content.status,
    }


@router.post("/analysis/{analysis_id}/async")
async def generate_content_async(
    analysis_id: UUID,
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Queue content generation as a background task.

    Returns immediately with task status.
    """
    # Verify analysis exists
    result = await db.execute(
        select(PostAnalysis).where(PostAnalysis.id == analysis_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Queue task
    from app.workers.generation_tasks import generate_content_for_analysis
    generate_content_for_analysis.delay(str(analysis_id), request.content_type)

    return {
        "status": "queued",
        "analysis_id": str(analysis_id),
        "content_type": request.content_type,
        "message": "Content generation queued. Check content endpoint for results.",
    }


@router.post("/content/{content_id}/regenerate")
async def regenerate_content(
    content_id: UUID,
    request: RegenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Regenerate content with different settings.

    Creates new media files for existing content.
    """
    # Fetch existing content
    result = await db.execute(
        select(GeneratedContent)
        .options(selectinload(GeneratedContent.post_analysis))
        .where(GeneratedContent.id == content_id)
    )
    content = result.scalar_one_or_none()

    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    if content.status == "published":
        raise HTTPException(
            status_code=400,
            detail="Cannot regenerate published content"
        )

    # Use same analysis to generate new content
    pipeline = ContentPipeline()
    new_content = await pipeline.generate_content(
        db,
        content.post_analysis_id,
        content_type=request.content_type or content.content_type,
    )

    if not new_content:
        raise HTTPException(status_code=500, detail="Regeneration failed")

    # Mark old content as rejected
    content.status = "rejected"
    await db.commit()

    return {
        "status": "success",
        "old_content_id": str(content_id),
        "new_content_id": str(new_content.id),
        "content_type": new_content.content_type,
    }


@router.get("/content/{content_id}/preview")
async def preview_content(
    content_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get content preview data.

    Returns content details and media URLs.
    """
    result = await db.execute(
        select(GeneratedContent)
        .options(
            selectinload(GeneratedContent.post_analysis)
            .selectinload(PostAnalysis.post)
        )
        .where(GeneratedContent.id == content_id)
    )
    content = result.scalar_one_or_none()

    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    return {
        "id": str(content.id),
        "content_type": content.content_type,
        "title": content.title,
        "caption": content.caption,
        "hashtags": content.hashtags,
        "media_urls": content.media_urls,
        "thumbnail_url": content.thumbnail_url,
        "status": content.status,
        "created_at": content.created_at.isoformat(),
        "metadata": content.generation_metadata,
    }


@router.get("/content/{content_id}/media/{slide_num}")
async def get_media_file(
    content_id: UUID,
    slide_num: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific media file from generated content.

    Args:
        content_id: Content UUID
        slide_num: Slide number (1-indexed)
    """
    result = await db.execute(
        select(GeneratedContent).where(GeneratedContent.id == content_id)
    )
    content = result.scalar_one_or_none()

    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    if not content.media_urls:
        raise HTTPException(status_code=404, detail="No media files")

    if slide_num < 1 or slide_num > len(content.media_urls):
        raise HTTPException(status_code=404, detail="Slide not found")

    media_path = content.media_urls[slide_num - 1]

    from pathlib import Path
    if not Path(media_path).exists():
        raise HTTPException(status_code=404, detail="Media file not found")

    return FileResponse(
        media_path,
        media_type="image/png",
        filename=f"{content_id}_slide_{slide_num}.png"
    )


@router.post("/queue/process")
async def process_generation_queue(
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
):
    """
    Process the content generation queue.

    Generates content for analyzed posts that haven't been processed.
    """
    # Find posts needing content
    result = await db.execute(
        select(Post)
        .options(selectinload(Post.analysis))
        .where(Post.is_analyzed == True)
        .where(Post.is_processed == False)
        .order_by(Post.viral_score.desc())
        .limit(limit)
    )
    posts = result.scalars().all()

    if not posts:
        return {"status": "empty", "processed": 0}

    processed = 0
    failed = 0

    for post in posts:
        if post.analysis:
            try:
                content = await generate_content_for_post(db, post.analysis.id)
                if content:
                    processed += 1
                else:
                    failed += 1
            except Exception as e:
                failed += 1

    return {
        "status": "completed",
        "processed": processed,
        "failed": failed,
    }


@router.get("/stats")
async def get_generation_stats(db: AsyncSession = Depends(get_db)):
    """Get content generation statistics."""
    from sqlalchemy import func

    # Count by status
    status_counts = await db.execute(
        select(GeneratedContent.status, func.count())
        .group_by(GeneratedContent.status)
    )

    # Count by type
    type_counts = await db.execute(
        select(GeneratedContent.content_type, func.count())
        .group_by(GeneratedContent.content_type)
    )

    # Pending generation (analyzed but not processed)
    pending = await db.scalar(
        select(func.count())
        .select_from(Post)
        .where(Post.is_analyzed == True)
        .where(Post.is_processed == False)
    )

    return {
        "by_status": {row[0]: row[1] for row in status_counts},
        "by_type": {row[0]: row[1] for row in type_counts},
        "pending_generation": pending,
    }
