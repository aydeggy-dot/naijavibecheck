"""
Database Storage Service

Production-ready storage that saves scraped comments and analysis
results to PostgreSQL instead of JSON files.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import uuid4
import hashlib

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert

from app.database import get_async_session
from app.models.celebrity import Celebrity
from app.models.post import Post
from app.models.comment import Comment
from app.models.analysis import CommentAnalysis, PostAnalysis

logger = logging.getLogger(__name__)


class DatabaseStorage:
    """
    Handles all database operations for the vibe check pipeline.

    This replaces JSON file storage with proper PostgreSQL storage.
    """

    def __init__(self, session: Optional[AsyncSession] = None):
        self._session = session

    async def get_session(self) -> AsyncSession:
        """Get or create database session."""
        if self._session:
            return self._session
        async for session in get_async_session():
            return session

    # =========================================
    # CELEBRITY OPERATIONS
    # =========================================

    async def get_or_create_celebrity(
        self,
        instagram_username: str,
        full_name: Optional[str] = None,
        category: Optional[str] = None
    ) -> Celebrity:
        """Get existing celebrity or create new one."""
        session = await self.get_session()

        # Try to find existing
        result = await session.execute(
            select(Celebrity).where(Celebrity.instagram_username == instagram_username)
        )
        celebrity = result.scalar_one_or_none()

        if celebrity:
            return celebrity

        # Create new
        celebrity = Celebrity(
            id=uuid4(),
            instagram_username=instagram_username,
            full_name=full_name or instagram_username,
            category=category or "entertainment",
            is_active=True
        )
        session.add(celebrity)
        await session.commit()
        await session.refresh(celebrity)

        logger.info(f"Created new celebrity: {instagram_username}")
        return celebrity

    # =========================================
    # POST OPERATIONS
    # =========================================

    async def get_or_create_post(
        self,
        celebrity_id,
        shortcode: str,
        caption: Optional[str] = None,
        comment_count: Optional[int] = None
    ) -> Post:
        """Get existing post or create new one."""
        session = await self.get_session()

        # Try to find existing
        result = await session.execute(
            select(Post).where(Post.shortcode == shortcode)
        )
        post = result.scalar_one_or_none()

        if post:
            # Update comment count if provided
            if comment_count:
                post.comment_count = comment_count
                await session.commit()
            return post

        # Create new
        post = Post(
            id=uuid4(),
            celebrity_id=celebrity_id,
            instagram_post_id=shortcode,
            shortcode=shortcode,
            post_url=f"https://www.instagram.com/p/{shortcode}/",
            caption=caption,
            comment_count=comment_count,
            scraped_at=datetime.utcnow()
        )
        session.add(post)
        await session.commit()
        await session.refresh(post)

        logger.info(f"Created new post: {shortcode}")
        return post

    # =========================================
    # COMMENT OPERATIONS
    # =========================================

    def _anonymize_username(self, username: str) -> str:
        """Create anonymized version of username for privacy."""
        hash_digest = hashlib.md5(username.encode()).hexdigest()[:8]
        return f"user_{hash_digest}"

    async def save_comments(
        self,
        post_id,
        comments: List[Dict[str, Any]],
        batch_size: int = 500
    ) -> int:
        """
        Save comments to database in batches.

        Args:
            post_id: The post UUID
            comments: List of comment dicts from scraper
            batch_size: Number of comments per batch

        Returns:
            Number of comments saved
        """
        session = await self.get_session()
        saved_count = 0

        for i in range(0, len(comments), batch_size):
            batch = comments[i:i + batch_size]

            for comment_data in batch:
                username = comment_data.get('username', 'unknown')

                comment = Comment(
                    id=uuid4(),
                    post_id=post_id,
                    instagram_comment_id=comment_data.get('id'),
                    username=username,
                    username_anonymized=self._anonymize_username(username),
                    text=comment_data.get('text', ''),
                    like_count=comment_data.get('likes', 0),
                    commented_at=comment_data.get('timestamp'),
                    scraped_at=datetime.utcnow(),
                    is_reply=comment_data.get('is_reply', False)
                )
                session.add(comment)
                saved_count += 1

            await session.commit()
            logger.info(f"Saved batch: {saved_count}/{len(comments)} comments")

        return saved_count

    async def get_comments_for_post(self, post_id) -> List[Comment]:
        """Get all comments for a post."""
        session = await self.get_session()

        result = await session.execute(
            select(Comment).where(Comment.post_id == post_id)
        )
        return result.scalars().all()

    # =========================================
    # ANALYSIS OPERATIONS
    # =========================================

    async def save_comment_analyses(
        self,
        analyses: List[Dict[str, Any]],
        batch_size: int = 500
    ) -> int:
        """
        Save individual comment analyses.

        Args:
            analyses: List of analysis results with comment_id
            batch_size: Batch size for commits

        Returns:
            Number of analyses saved
        """
        session = await self.get_session()
        saved_count = 0

        for i in range(0, len(analyses), batch_size):
            batch = analyses[i:i + batch_size]

            for analysis_data in batch:
                analysis = CommentAnalysis(
                    id=uuid4(),
                    comment_id=analysis_data['comment_id'],
                    sentiment=analysis_data.get('sentiment'),
                    sentiment_score=analysis_data.get('sentiment_score'),
                    toxicity_score=analysis_data.get('toxicity_score'),
                    analyzed_at=datetime.utcnow(),
                    analysis_metadata={
                        'method': analysis_data.get('analysis_method', 'local')
                    }
                )
                session.add(analysis)
                saved_count += 1

            await session.commit()

        logger.info(f"Saved {saved_count} comment analyses")
        return saved_count

    async def save_post_analysis(
        self,
        post_id,
        stats: Dict[str, Any],
        summary: Dict[str, Any],
        top_comments: Dict[str, List]
    ) -> PostAnalysis:
        """
        Save overall post analysis results.

        This is the main analysis record that stores:
        - Sentiment statistics
        - AI-generated summary
        - Top positive/negative comments
        """
        session = await self.get_session()

        # Check if analysis already exists
        result = await session.execute(
            select(PostAnalysis).where(PostAnalysis.post_id == post_id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing
            existing.total_comments_analyzed = stats.get('total', 0)
            existing.positive_count = stats.get('positive', 0)
            existing.negative_count = stats.get('negative', 0)
            existing.neutral_count = stats.get('neutral', 0)
            existing.positive_percentage = stats.get('positive_pct', 0)
            existing.negative_percentage = stats.get('negative_pct', 0)
            existing.neutral_percentage = stats.get('neutral_pct', 0)
            existing.headline = summary.get('headline')
            existing.vibe_summary = summary.get('vibe_summary')
            existing.controversy_level = summary.get('controversy_level')
            existing.themes = summary.get('themes', [])
            existing.recommended_hashtags = summary.get('recommended_hashtags', [])
            existing.top_positive_comments = top_comments.get('top_positive', [])
            existing.top_negative_comments = top_comments.get('top_negative', [])
            existing.notable_comments = top_comments.get('notable', [])
            existing.analyzed_at = datetime.utcnow()

            await session.commit()
            await session.refresh(existing)
            return existing

        # Create new
        analysis = PostAnalysis(
            id=uuid4(),
            post_id=post_id,
            total_comments_analyzed=stats.get('total', 0),
            positive_count=stats.get('positive', 0),
            negative_count=stats.get('negative', 0),
            neutral_count=stats.get('neutral', 0),
            positive_percentage=stats.get('positive_pct', 0),
            negative_percentage=stats.get('negative_pct', 0),
            neutral_percentage=stats.get('neutral_pct', 0),
            headline=summary.get('headline'),
            vibe_summary=summary.get('vibe_summary'),
            controversy_level=summary.get('controversy_level'),
            themes=summary.get('themes', []),
            recommended_hashtags=summary.get('recommended_hashtags', []),
            top_positive_comments=top_comments.get('top_positive', []),
            top_negative_comments=top_comments.get('top_negative', []),
            notable_comments=top_comments.get('notable', []),
            analyzed_at=datetime.utcnow()
        )
        session.add(analysis)
        await session.commit()
        await session.refresh(analysis)

        # Mark post as analyzed
        post_result = await session.execute(
            select(Post).where(Post.id == post_id)
        )
        post = post_result.scalar_one_or_none()
        if post:
            post.is_analyzed = True
            await session.commit()

        logger.info(f"Saved post analysis: {analysis.headline}")
        return analysis

    # =========================================
    # QUERY OPERATIONS
    # =========================================

    async def get_post_analysis(self, post_id) -> Optional[PostAnalysis]:
        """Get analysis for a post."""
        session = await self.get_session()

        result = await session.execute(
            select(PostAnalysis).where(PostAnalysis.post_id == post_id)
        )
        return result.scalar_one_or_none()

    async def get_recent_analyses(self, limit: int = 10) -> List[PostAnalysis]:
        """Get most recent analyses."""
        session = await self.get_session()

        result = await session.execute(
            select(PostAnalysis)
            .order_by(PostAnalysis.analyzed_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_analysis_stats(self) -> Dict[str, Any]:
        """Get overall platform statistics."""
        session = await self.get_session()

        # Total posts analyzed
        posts_result = await session.execute(
            select(func.count(PostAnalysis.id))
        )
        total_posts = posts_result.scalar() or 0

        # Total comments analyzed
        comments_result = await session.execute(
            select(func.sum(PostAnalysis.total_comments))
        )
        total_comments = comments_result.scalar() or 0

        # Average positivity
        avg_result = await session.execute(
            select(func.avg(PostAnalysis.positive_percentage))
        )
        avg_positive = avg_result.scalar() or 0

        return {
            'total_posts_analyzed': total_posts,
            'total_comments_analyzed': int(total_comments),
            'average_positivity': round(float(avg_positive), 1),
            'last_updated': datetime.utcnow().isoformat()
        }


# Convenience function for quick access
async def save_vibe_check_result(
    shortcode: str,
    celebrity_name: str,
    comments: List[Dict],
    stats: Dict[str, Any],
    summary: Dict[str, Any],
    top_comments: Dict[str, List]
) -> Dict[str, Any]:
    """
    One-call function to save complete vibe check results to database.

    This is what you call at the end of the pipeline.

    Returns:
        Dict with post_id and analysis_id
    """
    storage = DatabaseStorage()

    # 1. Get or create celebrity
    celebrity = await storage.get_or_create_celebrity(
        instagram_username=celebrity_name.lower().replace(' ', ''),
        full_name=celebrity_name
    )

    # 2. Get or create post
    post = await storage.get_or_create_post(
        celebrity_id=celebrity.id,
        shortcode=shortcode,
        comment_count=len(comments)
    )

    # 3. Save comments
    await storage.save_comments(post.id, comments)

    # 4. Save analysis
    analysis = await storage.save_post_analysis(
        post_id=post.id,
        stats=stats,
        summary=summary,
        top_comments=top_comments
    )

    logger.info(f"Saved complete vibe check: {shortcode} -> {analysis.headline}")

    return {
        'post_id': str(post.id),
        'analysis_id': str(analysis.id),
        'headline': analysis.headline
    }
