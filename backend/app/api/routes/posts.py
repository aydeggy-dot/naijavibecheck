"""Posts API endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.models import Celebrity, Post, Comment
from app.schemas.post import PostListResponse, PostResponse

router = APIRouter()


@router.get("", response_model=PostListResponse)
async def list_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    celebrity_id: Optional[UUID] = None,
    is_viral: Optional[bool] = None,
    is_analyzed: Optional[bool] = None,
    is_processed: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all posts with pagination and filtering."""
    query = select(Post).options(selectinload(Post.celebrity))

    # Apply filters
    if celebrity_id:
        query = query.where(Post.celebrity_id == celebrity_id)
    if is_viral is not None:
        query = query.where(Post.is_viral == is_viral)
    if is_analyzed is not None:
        query = query.where(Post.is_analyzed == is_analyzed)
    if is_processed is not None:
        query = query.where(Post.is_processed == is_processed)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Apply pagination
    query = query.order_by(Post.scraped_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    posts = result.scalars().all()

    items = [
        PostResponse(
            id=post.id,
            celebrity_id=post.celebrity_id,
            instagram_post_id=post.instagram_post_id,
            shortcode=post.shortcode,
            post_url=post.post_url,
            caption=post.caption,
            like_count=post.like_count,
            comment_count=post.comment_count,
            posted_at=post.posted_at,
            scraped_at=post.scraped_at,
            is_viral=post.is_viral,
            viral_score=post.viral_score,
            is_analyzed=post.is_analyzed,
            is_processed=post.is_processed,
            celebrity_username=post.celebrity.instagram_username if post.celebrity else None,
        )
        for post in posts
    ]

    return PostListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/viral", response_model=PostListResponse)
async def list_viral_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List viral posts that haven't been processed yet."""
    query = (
        select(Post)
        .options(selectinload(Post.celebrity))
        .where(Post.is_viral == True)
        .where(Post.is_processed == False)
    )

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    query = query.order_by(Post.viral_score.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    posts = result.scalars().all()

    items = [
        PostResponse(
            id=post.id,
            celebrity_id=post.celebrity_id,
            instagram_post_id=post.instagram_post_id,
            shortcode=post.shortcode,
            post_url=post.post_url,
            caption=post.caption,
            like_count=post.like_count,
            comment_count=post.comment_count,
            posted_at=post.posted_at,
            scraped_at=post.scraped_at,
            is_viral=post.is_viral,
            viral_score=post.viral_score,
            is_analyzed=post.is_analyzed,
            is_processed=post.is_processed,
            celebrity_username=post.celebrity.instagram_username if post.celebrity else None,
        )
        for post in posts
    ]

    return PostListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific post by ID."""
    result = await db.execute(
        select(Post).options(selectinload(Post.celebrity)).where(Post.id == post_id)
    )
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return PostResponse(
        id=post.id,
        celebrity_id=post.celebrity_id,
        instagram_post_id=post.instagram_post_id,
        shortcode=post.shortcode,
        post_url=post.post_url,
        caption=post.caption,
        like_count=post.like_count,
        comment_count=post.comment_count,
        posted_at=post.posted_at,
        scraped_at=post.scraped_at,
        is_viral=post.is_viral,
        viral_score=post.viral_score,
        is_analyzed=post.is_analyzed,
        is_processed=post.is_processed,
        celebrity_username=post.celebrity.instagram_username if post.celebrity else None,
    )


@router.get("/{post_id}/comments")
async def get_post_comments(
    post_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get comments for a specific post."""
    # Verify post exists
    post_result = await db.execute(select(Post).where(Post.id == post_id))
    if not post_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Post not found")

    query = select(Comment).where(Comment.post_id == post_id)

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    query = query.order_by(Comment.like_count.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    comments = result.scalars().all()

    return {
        "items": [
            {
                "id": c.id,
                "username_anonymized": c.username_anonymized,
                "text": c.text,
                "like_count": c.like_count,
                "commented_at": c.commented_at,
                "is_reply": c.is_reply,
            }
            for c in comments
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }
