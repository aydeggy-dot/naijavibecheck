"""Full analysis pipeline for Instagram posts."""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Post, Comment, CommentAnalysis, PostAnalysis, Celebrity
from app.services.analyzer.sentiment_analyzer import SentimentAnalyzer
from app.services.analyzer.comment_selector import CommentSelector
from app.services.analyzer.viral_scorer import ViralScorer

logger = logging.getLogger(__name__)


class AnalysisPipeline:
    """
    Full analysis pipeline for Instagram posts.

    Pipeline stages:
    1. Fetch post and comments from database
    2. Run sentiment analysis on all comments
    3. Select top positive and negative comments
    4. Calculate post-level statistics
    5. Generate AI summary and insights
    6. Store all results in database
    """

    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()
        self.comment_selector = CommentSelector()
        self.viral_scorer = ViralScorer()

    async def analyze_post(
        self,
        db: AsyncSession,
        post_id: UUID,
        max_comments: int = 500,
    ) -> Optional[PostAnalysis]:
        """
        Run the full analysis pipeline for a post.

        Args:
            db: Database session
            post_id: Post UUID to analyze
            max_comments: Maximum comments to analyze

        Returns:
            PostAnalysis object or None if failed
        """
        logger.info(f"Starting analysis pipeline for post {post_id}")

        # Stage 1: Fetch post and comments
        post = await self._fetch_post_with_comments(db, post_id, max_comments)
        if not post:
            logger.error(f"Post {post_id} not found")
            return None

        if not post.comments:
            logger.warning(f"Post {post_id} has no comments to analyze")
            return None

        celebrity_name = post.celebrity.full_name or post.celebrity.instagram_username

        # Stage 2: Run sentiment analysis
        comments_data = [
            {
                "id": str(c.id),
                "username_anonymized": c.username_anonymized,
                "text": c.text,
                "like_count": c.like_count,
            }
            for c in post.comments
        ]

        analyzed_comments = await self.sentiment_analyzer.analyze_comments_batch(
            comments=comments_data,
            celebrity_name=celebrity_name,
            post_context=post.caption or "",
        )

        # Stage 3: Store individual comment analyses
        await self._store_comment_analyses(db, post.comments, analyzed_comments)

        # Stage 4: Select top comments
        top_positive, top_negative = self.comment_selector.select_top_comments(
            analyzed_comments, top_n=3
        )

        # Stage 5: Calculate post-level statistics
        stats = self._calculate_stats(analyzed_comments)

        # Stage 6: Generate AI summary
        ai_insights = await self.sentiment_analyzer.generate_post_summary(
            celebrity_name=celebrity_name,
            post_caption=post.caption or "",
            stats=stats,
            top_positive=top_positive,
            top_negative=top_negative,
        )

        # Stage 7: Store post analysis
        post_analysis = await self._store_post_analysis(
            db=db,
            post=post,
            stats=stats,
            top_positive=top_positive,
            top_negative=top_negative,
            ai_insights=ai_insights,
        )

        # Mark post as analyzed
        post.is_analyzed = True
        await db.commit()

        logger.info(f"Completed analysis pipeline for post {post_id}")
        return post_analysis

    async def _fetch_post_with_comments(
        self,
        db: AsyncSession,
        post_id: UUID,
        max_comments: int,
    ) -> Optional[Post]:
        """Fetch post with celebrity and comments."""
        result = await db.execute(
            select(Post)
            .options(
                selectinload(Post.celebrity),
                selectinload(Post.comments),
            )
            .where(Post.id == post_id)
        )
        post = result.scalar_one_or_none()

        if post and len(post.comments) > max_comments:
            # Sort by likes and take top comments
            post.comments = sorted(
                post.comments,
                key=lambda c: c.like_count or 0,
                reverse=True,
            )[:max_comments]

        return post

    async def _store_comment_analyses(
        self,
        db: AsyncSession,
        comments: List[Comment],
        analyzed_data: List[Dict],
    ):
        """Store sentiment analysis results for each comment."""
        # Create lookup by comment ID
        analysis_by_id = {d.get("id"): d for d in analyzed_data}

        for comment in comments:
            analysis_data = analysis_by_id.get(str(comment.id))
            if not analysis_data:
                continue

            # Check if analysis already exists
            existing = await db.execute(
                select(CommentAnalysis).where(CommentAnalysis.comment_id == comment.id)
            )
            if existing.scalar_one_or_none():
                continue

            comment_analysis = CommentAnalysis(
                comment_id=comment.id,
                sentiment=analysis_data.get("sentiment", "neutral"),
                sentiment_score=analysis_data.get("sentiment_score", 0),
                toxicity_score=analysis_data.get("toxicity_score", 0),
                emotion_tags=analysis_data.get("emotion_tags", []),
                is_top_positive=False,
                is_top_negative=False,
                analysis_metadata={
                    "ai_summary": analysis_data.get("ai_summary"),
                    "is_notable": analysis_data.get("is_notable", False),
                },
            )
            db.add(comment_analysis)

        await db.flush()

    def _calculate_stats(self, analyzed_comments: List[Dict]) -> Dict[str, Any]:
        """Calculate aggregate statistics from analyzed comments."""
        total = len(analyzed_comments)
        if total == 0:
            return {
                "total": 0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
                "positive_pct": 0,
                "negative_pct": 0,
                "neutral_pct": 0,
                "avg_sentiment": 0,
                "avg_toxicity": 0,
            }

        positive = sum(1 for c in analyzed_comments if c.get("sentiment") == "positive")
        negative = sum(1 for c in analyzed_comments if c.get("sentiment") == "negative")
        neutral = total - positive - negative

        avg_sentiment = sum(c.get("sentiment_score", 0) for c in analyzed_comments) / total
        avg_toxicity = sum(c.get("toxicity_score", 0) for c in analyzed_comments) / total

        return {
            "total": total,
            "positive_count": positive,
            "negative_count": negative,
            "neutral_count": neutral,
            "positive_pct": round((positive / total) * 100, 1),
            "negative_pct": round((negative / total) * 100, 1),
            "neutral_pct": round((neutral / total) * 100, 1),
            "avg_sentiment": round(avg_sentiment, 3),
            "avg_toxicity": round(avg_toxicity, 3),
        }

    async def _store_post_analysis(
        self,
        db: AsyncSession,
        post: Post,
        stats: Dict,
        top_positive: List[Dict],
        top_negative: List[Dict],
        ai_insights: Dict,
    ) -> PostAnalysis:
        """Store the post-level analysis."""
        # Get comment UUIDs for top comments
        top_positive_ids = [UUID(c["id"]) for c in top_positive if c.get("id")]
        top_negative_ids = [UUID(c["id"]) for c in top_negative if c.get("id")]

        # Mark top comments in their analyses
        for comment_id in top_positive_ids:
            result = await db.execute(
                select(CommentAnalysis).where(CommentAnalysis.comment_id == comment_id)
            )
            analysis = result.scalar_one_or_none()
            if analysis:
                analysis.is_top_positive = True

        for comment_id in top_negative_ids:
            result = await db.execute(
                select(CommentAnalysis).where(CommentAnalysis.comment_id == comment_id)
            )
            analysis = result.scalar_one_or_none()
            if analysis:
                analysis.is_top_negative = True

        # Calculate controversy score
        controversy_score = self._calculate_controversy_score(stats)

        # Check if analysis already exists
        existing = await db.execute(
            select(PostAnalysis).where(PostAnalysis.post_id == post.id)
        )
        post_analysis = existing.scalar_one_or_none()

        if post_analysis:
            # Update existing
            post_analysis.total_comments_analyzed = stats["total"]
            post_analysis.positive_count = stats["positive_count"]
            post_analysis.negative_count = stats["negative_count"]
            post_analysis.neutral_count = stats["neutral_count"]
            post_analysis.positive_percentage = stats["positive_pct"]
            post_analysis.negative_percentage = stats["negative_pct"]
            post_analysis.neutral_percentage = stats["neutral_pct"]
            post_analysis.average_sentiment_score = stats["avg_sentiment"]
            post_analysis.top_positive_comment_ids = top_positive_ids or None
            post_analysis.top_negative_comment_ids = top_negative_ids or None
            post_analysis.controversy_score = controversy_score
            post_analysis.analyzed_at = datetime.utcnow()
            post_analysis.ai_summary = ai_insights.get("vibe_summary", "")
            post_analysis.ai_insights = ai_insights
        else:
            # Create new
            post_analysis = PostAnalysis(
                post_id=post.id,
                total_comments_analyzed=stats["total"],
                positive_count=stats["positive_count"],
                negative_count=stats["negative_count"],
                neutral_count=stats["neutral_count"],
                positive_percentage=stats["positive_pct"],
                negative_percentage=stats["negative_pct"],
                neutral_percentage=stats["neutral_pct"],
                average_sentiment_score=stats["avg_sentiment"],
                top_positive_comment_ids=top_positive_ids or None,
                top_negative_comment_ids=top_negative_ids or None,
                controversy_score=controversy_score,
                ai_summary=ai_insights.get("vibe_summary", ""),
                ai_insights=ai_insights,
            )
            db.add(post_analysis)

        await db.flush()
        return post_analysis

    def _calculate_controversy_score(self, stats: Dict) -> float:
        """
        Calculate how controversial/divisive the post is.

        High controversy = roughly equal positive and negative comments.
        """
        if stats["total"] == 0:
            return 0.0

        positive_ratio = stats["positive_pct"] / 100
        negative_ratio = stats["negative_pct"] / 100

        # Maximum controversy when both are equal (around 40-50% each)
        # Using standard deviation from 0.5 as measure
        balance = 1 - abs(positive_ratio - negative_ratio)

        # Also consider toxicity
        toxicity_factor = stats.get("avg_toxicity", 0) * 0.5

        controversy = (balance * 0.7 + toxicity_factor * 0.3) * 100
        return round(min(controversy, 100), 2)


async def run_analysis_pipeline(
    db: AsyncSession,
    post_id: UUID,
) -> Optional[PostAnalysis]:
    """
    Convenience function to run the analysis pipeline.

    Args:
        db: Database session
        post_id: Post UUID

    Returns:
        PostAnalysis or None
    """
    pipeline = AnalysisPipeline()
    return await pipeline.analyze_post(db, post_id)
