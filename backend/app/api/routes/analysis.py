"""Analysis API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.models import Post, Comment, PostAnalysis, CommentAnalysis
from app.services.analyzer import (
    AnalysisPipeline,
    ViralScorer,
    TrendingDetector,
    run_analysis_pipeline,
)

router = APIRouter()


def format_analysis_response(a, include_comments=False):
    """Format a PostAnalysis object for API response."""
    from app.models import Post, Celebrity

    # Get celebrity name from post relationship
    celebrity_name = None
    post_url = None
    if a.post:
        post_url = a.post.post_url or f"https://www.instagram.com/p/{a.post.shortcode}/"
        if hasattr(a.post, 'celebrity') and a.post.celebrity:
            celebrity_name = a.post.celebrity.full_name or a.post.celebrity.instagram_username

    return {
        "id": str(a.id),
        "post_id": str(a.post_id),
        "celebrity_name": celebrity_name,
        "post_url": post_url,
        "overall_sentiment": "positive" if (a.positive_percentage or 0) > (a.negative_percentage or 0) else (
            "negative" if (a.negative_percentage or 0) > (a.positive_percentage or 0) else "neutral"
        ),
        "sentiment_breakdown": {
            "positive": a.positive_percentage or 0,
            "negative": a.negative_percentage or 0,
            "neutral": a.neutral_percentage or 0,
        },
        "total_comments": a.total_comments_analyzed or 0,
        # New fields from cost-effective analyzer
        "headline": a.headline,
        "vibe_summary": a.vibe_summary,
        "spicy_take": a.spicy_take,
        "controversy_level": a.controversy_level,
        "themes": a.themes or [],
        "recommended_hashtags": a.recommended_hashtags or [],
        # Comments (optional)
        "top_positive_comments": a.top_positive_comments if include_comments else [],
        "top_negative_comments": a.top_negative_comments if include_comments else [],
        "notable_comments": a.notable_comments if include_comments else [],
        # Legacy fields
        "controversy_score": a.controversy_score or 0,
        "viral_potential": (a.post.viral_score or 0) / 100 if a.post else 0,
        "key_themes": a.ai_insights.get("key_themes", []) if a.ai_insights else [],
        "key_insights": a.ai_insights.get("key_insights", []) if a.ai_insights else [],
        "summary": a.ai_summary or a.vibe_summary,
        "analyzed_at": a.analyzed_at.isoformat() if a.analyzed_at else None,
        "analysis_method": a.analysis_method,
        "analysis_cost": a.analysis_cost,
    }


@router.get("/recent")
async def get_recent_analyses(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """Get recent post analyses."""
    from app.models import Celebrity

    result = await db.execute(
        select(PostAnalysis)
        .options(
            selectinload(PostAnalysis.post).selectinload(Post.celebrity)
        )
        .order_by(PostAnalysis.analyzed_at.desc())
        .limit(limit)
    )
    analyses = result.scalars().all()

    return [format_analysis_response(a) for a in analyses]


@router.get("/{analysis_id}")
async def get_analysis_by_id(
    analysis_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific analysis by ID with full details."""
    from app.models import Celebrity

    result = await db.execute(
        select(PostAnalysis)
        .options(
            selectinload(PostAnalysis.post).selectinload(Post.celebrity)
        )
        .where(PostAnalysis.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return format_analysis_response(analysis, include_comments=True)


@router.post("/posts/{post_id}/analyze")
async def trigger_post_analysis(
    post_id: UUID,
    background_tasks: BackgroundTasks,
    use_claude: bool = True,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger analysis for a specific post.

    Args:
        post_id: Post UUID
        use_claude: Use Claude API for full analysis (True) or simple rules (False)
    """
    # Verify post exists
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.is_analyzed:
        raise HTTPException(status_code=400, detail="Post already analyzed")

    if use_claude:
        # Run full analysis with Claude API
        analysis = await run_analysis_pipeline(db, post_id)
        if analysis:
            return {
                "status": "completed",
                "post_id": str(post_id),
                "analysis_id": str(analysis.id),
                "stats": {
                    "total": analysis.total_comments_analyzed,
                    "positive_pct": analysis.positive_percentage,
                    "negative_pct": analysis.negative_percentage,
                    "neutral_pct": analysis.neutral_percentage,
                },
            }
        raise HTTPException(status_code=500, detail="Analysis failed")
    else:
        # Queue background task for simple analysis
        from app.workers.analysis_tasks import analyze_post_sync

        analyze_post_sync.delay(str(post_id))
        return {
            "status": "queued",
            "post_id": str(post_id),
            "message": "Analysis task queued",
        }


@router.get("/posts/{post_id}/results")
async def get_analysis_results(
    post_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get full analysis results for a post.
    """
    # Get post analysis
    result = await db.execute(
        select(PostAnalysis)
        .options(selectinload(PostAnalysis.post))
        .where(PostAnalysis.post_id == post_id)
    )
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Get top positive comments
    top_positive = []
    if analysis.top_positive_comment_ids:
        result = await db.execute(
            select(Comment)
            .options(selectinload(Comment.analysis))
            .where(Comment.id.in_(analysis.top_positive_comment_ids))
        )
        for comment in result.scalars().all():
            top_positive.append({
                "id": str(comment.id),
                "username": comment.username_anonymized,
                "text": comment.text,
                "likes": comment.like_count,
                "sentiment_score": comment.analysis.sentiment_score if comment.analysis else None,
                "emotion_tags": comment.analysis.emotion_tags if comment.analysis else [],
            })

    # Get top negative comments
    top_negative = []
    if analysis.top_negative_comment_ids:
        result = await db.execute(
            select(Comment)
            .options(selectinload(Comment.analysis))
            .where(Comment.id.in_(analysis.top_negative_comment_ids))
        )
        for comment in result.scalars().all():
            top_negative.append({
                "id": str(comment.id),
                "username": comment.username_anonymized,
                "text": comment.text,
                "likes": comment.like_count,
                "toxicity_score": comment.analysis.toxicity_score if comment.analysis else None,
                "emotion_tags": comment.analysis.emotion_tags if comment.analysis else [],
            })

    return {
        "post_id": str(post_id),
        "analysis_id": str(analysis.id),
        "analyzed_at": analysis.analyzed_at.isoformat(),
        "stats": {
            "total_comments": analysis.total_comments_analyzed,
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
            "average_sentiment": analysis.average_sentiment_score,
            "controversy_score": analysis.controversy_score,
        },
        "ai_summary": analysis.ai_summary,
        "ai_insights": analysis.ai_insights,
        "top_positive_comments": top_positive,
        "top_negative_comments": top_negative,
    }


@router.post("/posts/{post_id}/viral-check")
async def check_viral_status(
    post_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Check and update viral status for a post.
    """
    result = await db.execute(
        select(Post)
        .options(selectinload(Post.celebrity))
        .where(Post.id == post_id)
    )
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    viral_scorer = ViralScorer()
    follower_count = post.celebrity.follower_count if post.celebrity else None

    analysis = viral_scorer.analyze_post(
        post_data={
            "like_count": post.like_count,
            "comment_count": post.comment_count,
            "posted_at": post.posted_at,
        },
        follower_count=follower_count,
    )

    # Update post
    post.viral_score = analysis["viral_score"]
    post.is_viral = analysis["is_viral"]
    await db.commit()

    return {
        "post_id": str(post_id),
        "shortcode": post.shortcode,
        **analysis,
    }


@router.get("/trending/celebrities")
async def get_trending_celebrities(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """
    Get currently trending celebrities based on viral posts.
    """
    detector = TrendingDetector()
    trending = await detector.get_trending_celebrities(db, limit=limit)
    return {"trending": trending, "count": len(trending)}


@router.get("/trending/posts")
async def get_trending_posts(
    limit: int = 20,
    min_score: float = 50.0,
    db: AsyncSession = Depends(get_db),
):
    """
    Get currently trending/hot posts.
    """
    detector = TrendingDetector()
    hot_posts = await detector.get_hot_posts(db, limit=limit, min_viral_score=min_score)
    return {"posts": hot_posts, "count": len(hot_posts)}


@router.get("/queue/unanalyzed")
async def get_unanalyzed_posts(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """
    Get viral posts that haven't been analyzed yet.
    """
    detector = TrendingDetector()
    posts = await detector.get_unanalyzed_viral_posts(db, limit=limit)

    return {
        "posts": [
            {
                "id": str(p.id),
                "shortcode": p.shortcode,
                "likes": p.like_count,
                "comments": p.comment_count,
                "viral_score": p.viral_score,
            }
            for p in posts
        ],
        "count": len(posts),
    }


@router.post("/queue/process")
async def process_analysis_queue(
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
):
    """
    Process the analysis queue - analyze pending posts.
    """
    detector = TrendingDetector()
    posts = await detector.get_unanalyzed_viral_posts(db, limit=limit)

    if not posts:
        return {"status": "empty", "processed": 0}

    pipeline = AnalysisPipeline()
    processed = 0
    failed = 0

    for post in posts:
        try:
            await pipeline.analyze_post(db, post.id)
            processed += 1
        except Exception as e:
            failed += 1

    return {
        "status": "completed",
        "processed": processed,
        "failed": failed,
    }
