"""Celery tasks for sentiment analysis."""

import logging
from uuid import UUID

import anthropic
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.workers.celery_app import celery_app
from app.database import SyncSessionLocal
from app.models import Post, Comment, CommentAnalysis, PostAnalysis, Celebrity
from app.services.analyzer.viral_scorer import ViralScorer

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def process_pending_analyses(self):
    """
    Find viral posts that need analysis and queue them.
    """
    logger.info("Processing pending analyses")

    try:
        db = SyncSessionLocal()

        # Find viral posts that haven't been analyzed
        pending_posts = (
            db.query(Post)
            .filter(Post.is_viral == True)
            .filter(Post.is_analyzed == False)
            .order_by(Post.viral_score.desc())
            .limit(10)
            .all()
        )

        logger.info(f"Found {len(pending_posts)} posts pending analysis")

        for post in pending_posts:
            analyze_post_sync.delay(str(post.id))

        db.close()
        return {"status": "queued", "posts": len(pending_posts)}

    except Exception as e:
        logger.error(f"Error processing pending analyses: {e}")
        raise


@celery_app.task(bind=True, max_retries=3)
def analyze_post_sync(self, post_id: str):
    """
    Analyze a post's comments for sentiment (sync version for Celery).

    This runs the full analysis pipeline:
    1. Fetch post and comments
    2. Run sentiment analysis via Claude API
    3. Select top positive/negative comments
    4. Calculate statistics
    5. Generate AI summary
    6. Store results
    """
    logger.info(f"Analyzing post: {post_id}")

    try:
        db = SyncSessionLocal()

        # Fetch post with comments
        post = (
            db.query(Post)
            .options(
                selectinload(Post.celebrity),
                selectinload(Post.comments),
            )
            .filter(Post.id == post_id)
            .first()
        )

        if not post:
            logger.warning(f"Post {post_id} not found")
            db.close()
            return {"status": "not_found"}

        if not post.comments:
            logger.warning(f"Post {post_id} has no comments")
            post.is_analyzed = True
            db.commit()
            db.close()
            return {"status": "no_comments"}

        celebrity_name = post.celebrity.full_name or post.celebrity.instagram_username
        logger.info(f"Analyzing {len(post.comments)} comments for {celebrity_name}")

        # For sync Celery task, we'll do a simplified analysis
        # The full async pipeline can be used from the API
        comments_analyzed = 0
        positive_count = 0
        negative_count = 0
        neutral_count = 0

        # Process comments (simplified without Claude for sync task)
        for comment in post.comments[:500]:
            # Check if already analyzed
            existing = (
                db.query(CommentAnalysis)
                .filter(CommentAnalysis.comment_id == comment.id)
                .first()
            )
            if existing:
                comments_analyzed += 1
                if existing.sentiment == "positive":
                    positive_count += 1
                elif existing.sentiment == "negative":
                    negative_count += 1
                else:
                    neutral_count += 1
                continue

            # Simple heuristic analysis (placeholder for Claude)
            sentiment, score, toxicity = _simple_sentiment_analysis(comment.text)

            analysis = CommentAnalysis(
                comment_id=comment.id,
                sentiment=sentiment,
                sentiment_score=score,
                toxicity_score=toxicity,
                emotion_tags=[],
            )
            db.add(analysis)
            comments_analyzed += 1

            if sentiment == "positive":
                positive_count += 1
            elif sentiment == "negative":
                negative_count += 1
            else:
                neutral_count += 1

        # Calculate stats
        total = comments_analyzed or 1
        stats = {
            "total": total,
            "positive_pct": round((positive_count / total) * 100, 1),
            "negative_pct": round((negative_count / total) * 100, 1),
            "neutral_pct": round((neutral_count / total) * 100, 1),
        }

        # Create or update post analysis
        post_analysis = (
            db.query(PostAnalysis)
            .filter(PostAnalysis.post_id == post.id)
            .first()
        )

        if post_analysis:
            post_analysis.total_comments_analyzed = comments_analyzed
            post_analysis.positive_count = positive_count
            post_analysis.negative_count = negative_count
            post_analysis.neutral_count = neutral_count
            post_analysis.positive_percentage = stats["positive_pct"]
            post_analysis.negative_percentage = stats["negative_pct"]
            post_analysis.neutral_percentage = stats["neutral_pct"]
        else:
            post_analysis = PostAnalysis(
                post_id=post.id,
                total_comments_analyzed=comments_analyzed,
                positive_count=positive_count,
                negative_count=negative_count,
                neutral_count=neutral_count,
                positive_percentage=stats["positive_pct"],
                negative_percentage=stats["negative_pct"],
                neutral_percentage=stats["neutral_pct"],
            )
            db.add(post_analysis)

        # Mark post as analyzed
        post.is_analyzed = True
        db.commit()
        db.close()

        logger.info(f"Completed analysis for post {post_id}: {stats}")
        return {
            "status": "success",
            "post_id": post_id,
            "comments_analyzed": comments_analyzed,
            "stats": stats,
        }

    except Exception as e:
        logger.error(f"Error analyzing post {post_id}: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True)
def update_viral_scores(self):
    """
    Recalculate viral scores for recent posts.
    """
    logger.info("Updating viral scores")

    try:
        db = SyncSessionLocal()
        viral_scorer = ViralScorer()

        # Get recent posts that might be viral
        posts = (
            db.query(Post)
            .options(selectinload(Post.celebrity))
            .filter(Post.is_viral == False)
            .order_by(Post.scraped_at.desc())
            .limit(100)
            .all()
        )

        updated = 0
        newly_viral = 0

        for post in posts:
            follower_count = post.celebrity.follower_count if post.celebrity else None

            analysis = viral_scorer.analyze_post(
                post_data={
                    "like_count": post.like_count,
                    "comment_count": post.comment_count,
                    "posted_at": post.posted_at,
                },
                follower_count=follower_count,
            )

            post.viral_score = analysis["viral_score"]

            if analysis["is_viral"] and not post.is_viral:
                post.is_viral = True
                newly_viral += 1
                logger.info(
                    f"New viral post detected: {post.shortcode} "
                    f"(score: {analysis['viral_score']})"
                )

            updated += 1

        db.commit()
        db.close()

        logger.info(f"Updated {updated} posts, {newly_viral} newly viral")
        return {
            "status": "success",
            "updated": updated,
            "newly_viral": newly_viral,
        }

    except Exception as e:
        logger.error(f"Error updating viral scores: {e}")
        raise


@celery_app.task(bind=True, max_retries=3)
def run_full_analysis_with_claude(self, post_id: str):
    """
    Run full analysis with Claude API (async wrapper).

    This queues the full analysis pipeline that uses Claude.
    """
    import asyncio
    from app.database import AsyncSessionLocal
    from app.services.analyzer.analysis_pipeline import run_analysis_pipeline
    from app.config import settings

    logger.info(f"Running full Claude analysis for post {post_id}")

    # Check if Claude API is configured
    if not settings.anthropic_api_key:
        logger.warning("ANTHROPIC_API_KEY not configured, skipping Claude analysis")
        return {
            "status": "skipped",
            "post_id": post_id,
            "reason": "ANTHROPIC_API_KEY not configured",
        }

    async def _run():
        async with AsyncSessionLocal() as db:
            result = await run_analysis_pipeline(db, UUID(post_id))
            await db.commit()
            return result

    try:
        result = asyncio.run(_run())
        if result:
            logger.info(f"Successfully analyzed post {post_id} with Claude")
            return {
                "status": "success",
                "post_id": post_id,
                "analysis_id": str(result.id),
            }
        logger.warning(f"Analysis returned no result for post {post_id}")
        return {"status": "failed", "post_id": post_id, "reason": "no_result"}

    except anthropic.RateLimitError as e:
        logger.warning(f"Claude API rate limit hit for post {post_id}: {e}")
        raise self.retry(exc=e, countdown=300)  # Wait 5 minutes

    except anthropic.APIError as e:
        logger.error(f"Claude API error for post {post_id}: {e}")
        raise self.retry(exc=e, countdown=120)

    except Exception as e:
        logger.error(f"Error in full analysis for post {post_id}: {e}")
        raise self.retry(exc=e, countdown=120)


def _simple_sentiment_analysis(text: str) -> tuple:
    """
    Simple rule-based sentiment analysis (fallback when Claude unavailable).

    Returns: (sentiment, score, toxicity)
    """
    text_lower = text.lower()

    # Positive indicators
    positive_words = [
        "love", "beautiful", "amazing", "great", "awesome", "best",
        "fire", "slay", "queen", "king", "legend", "proud", "support",
        "🔥", "❤️", "💯", "😍", "👏", "🙌", "💪", "👑",
    ]

    # Negative indicators
    negative_words = [
        "hate", "terrible", "worst", "ugly", "fake", "fraud", "shame",
        "disgusting", "trash", "rubbish", "stupid", "fool", "idiot",
        "😡", "🤮", "👎", "💔",
    ]

    # Toxic indicators
    toxic_words = [
        "stupid", "idiot", "fool", "dumb", "trash", "rubbish",
        "shut up", "die", "kill", "hate you",
    ]

    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    toxic_count = sum(1 for word in toxic_words if word in text_lower)

    # Calculate sentiment
    if positive_count > negative_count:
        sentiment = "positive"
        score = min(positive_count * 0.2, 1.0)
    elif negative_count > positive_count:
        sentiment = "negative"
        score = max(-negative_count * 0.2, -1.0)
    else:
        sentiment = "neutral"
        score = 0.0

    # Calculate toxicity
    toxicity = min(toxic_count * 0.3, 1.0)

    return sentiment, score, toxicity
