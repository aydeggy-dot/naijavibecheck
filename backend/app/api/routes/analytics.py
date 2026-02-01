"""Analytics API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.models import (
    Celebrity,
    Post,
    Comment,
    PostAnalysis,
    CommentAnalysis,
    GeneratedContent,
    OurEngagement,
)

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Get dashboard overview statistics."""
    # Count celebrities
    celeb_count = await db.scalar(
        select(func.count()).select_from(Celebrity).where(Celebrity.is_active == True)
    )

    # Count posts
    total_posts = await db.scalar(select(func.count()).select_from(Post))
    viral_posts = await db.scalar(
        select(func.count()).select_from(Post).where(Post.is_viral == True)
    )
    analyzed_posts = await db.scalar(
        select(func.count()).select_from(Post).where(Post.is_analyzed == True)
    )

    # Count comments
    total_comments = await db.scalar(select(func.count()).select_from(Comment))

    # Count generated content by status
    content_stats = await db.execute(
        select(GeneratedContent.status, func.count())
        .group_by(GeneratedContent.status)
    )
    content_by_status = {row[0]: row[1] for row in content_stats}

    return {
        "celebrities": {
            "total_active": celeb_count,
        },
        "posts": {
            "total": total_posts,
            "viral": viral_posts,
            "analyzed": analyzed_posts,
        },
        "comments": {
            "total": total_comments,
        },
        "content": {
            "draft": content_by_status.get("draft", 0),
            "pending_review": content_by_status.get("pending_review", 0),
            "approved": content_by_status.get("approved", 0),
            "published": content_by_status.get("published", 0),
            "rejected": content_by_status.get("rejected", 0),
        },
    }


@router.get("/posts/{post_id}")
async def get_post_analytics(
    post_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get detailed analytics for a specific post."""
    # Get post with analysis
    result = await db.execute(
        select(Post)
        .options(selectinload(Post.analysis), selectinload(Post.celebrity))
        .where(Post.id == post_id)
    )
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if not post.analysis:
        raise HTTPException(status_code=404, detail="Post has not been analyzed yet")

    analysis = post.analysis

    # Get top positive comments
    top_positive = []
    if analysis.top_positive_comment_ids:
        result = await db.execute(
            select(Comment)
            .options(selectinload(Comment.analysis))
            .where(Comment.id.in_(analysis.top_positive_comment_ids))
        )
        top_positive = [
            {
                "id": c.id,
                "username_anonymized": c.username_anonymized,
                "text": c.text,
                "like_count": c.like_count,
                "sentiment_score": c.analysis.sentiment_score if c.analysis else None,
            }
            for c in result.scalars().all()
        ]

    # Get top negative comments
    top_negative = []
    if analysis.top_negative_comment_ids:
        result = await db.execute(
            select(Comment)
            .options(selectinload(Comment.analysis))
            .where(Comment.id.in_(analysis.top_negative_comment_ids))
        )
        top_negative = [
            {
                "id": c.id,
                "username_anonymized": c.username_anonymized,
                "text": c.text,
                "like_count": c.like_count,
                "toxicity_score": c.analysis.toxicity_score if c.analysis else None,
            }
            for c in result.scalars().all()
        ]

    return {
        "post": {
            "id": post.id,
            "shortcode": post.shortcode,
            "caption": post.caption,
            "like_count": post.like_count,
            "comment_count": post.comment_count,
            "celebrity": post.celebrity.instagram_username if post.celebrity else None,
        },
        "analysis": {
            "total_comments_analyzed": analysis.total_comments_analyzed,
            "sentiment_breakdown": {
                "positive": {
                    "count": analysis.positive_count,
                    "percentage": analysis.positive_percentage,
                },
                "negative": {
                    "count": analysis.negative_count,
                    "percentage": analysis.negative_percentage,
                },
                "neutral": {
                    "count": analysis.neutral_count,
                    "percentage": analysis.neutral_percentage,
                },
            },
            "average_sentiment_score": analysis.average_sentiment_score,
            "controversy_score": analysis.controversy_score,
            "ai_summary": analysis.ai_summary,
            "ai_insights": analysis.ai_insights,
            "analyzed_at": analysis.analyzed_at,
        },
        "top_positive_comments": top_positive,
        "top_negative_comments": top_negative,
    }


@router.get("/trending")
async def get_trending(
    type: str = None,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """Get trending celebrities, posts, or topics."""
    items = []

    if type is None or type == "celebrities":
        # Get celebrities sorted by recent viral posts
        result = await db.execute(
            select(Celebrity)
            .where(Celebrity.is_active == True)
            .order_by(Celebrity.follower_count.desc())
            .limit(limit)
        )
        celebrities = result.scalars().all()

        for i, celeb in enumerate(celebrities):
            # Calculate a trending score based on followers
            base_score = min(100, (celeb.follower_count or 0) / 300000)
            change = (5 - i) * 3  # Higher ranked = positive change

            items.append({
                "id": str(celeb.id),
                "name": celeb.full_name or celeb.instagram_username,
                "type": "celebrity",
                "score": base_score,
                "change": change,
                "metadata": {
                    "username": celeb.instagram_username,
                    "follower_count": celeb.follower_count,
                    "category": celeb.category,
                },
            })

    elif type == "posts":
        # Get viral posts
        result = await db.execute(
            select(Post)
            .options(selectinload(Post.celebrity))
            .where(Post.is_viral == True)
            .order_by(Post.viral_score.desc())
            .limit(limit)
        )
        posts = result.scalars().all()

        for post in posts:
            items.append({
                "id": str(post.id),
                "name": post.celebrity.instagram_username if post.celebrity else "Unknown",
                "type": "post",
                "score": post.viral_score or 0,
                "change": 0,
                "metadata": {
                    "shortcode": post.shortcode,
                    "like_count": post.like_count,
                    "comment_count": post.comment_count,
                },
            })

    return items


@router.get("/our-engagement")
async def get_our_engagement_stats(db: AsyncSession = Depends(get_db)):
    """Get engagement statistics for our published content."""
    # Get published content with engagement
    result = await db.execute(
        select(GeneratedContent)
        .options(selectinload(GeneratedContent.engagement))
        .where(GeneratedContent.status == "published")
        .order_by(GeneratedContent.published_at.desc())
        .limit(20)
    )
    content_list = result.scalars().all()

    items = []
    for content in content_list:
        latest_engagement = None
        if content.engagement:
            latest_engagement = max(content.engagement, key=lambda e: e.checked_at)

        items.append({
            "id": content.id,
            "title": content.title,
            "content_type": content.content_type,
            "published_at": content.published_at,
            "engagement": {
                "likes": latest_engagement.like_count if latest_engagement else 0,
                "comments": latest_engagement.comment_count if latest_engagement else 0,
                "shares": latest_engagement.share_count if latest_engagement else 0,
                "saves": latest_engagement.save_count if latest_engagement else 0,
                "engagement_rate": latest_engagement.engagement_rate if latest_engagement else 0,
            } if latest_engagement else None,
        })

    return {"items": items, "total": len(items)}
