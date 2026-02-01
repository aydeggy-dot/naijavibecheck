"""Trending topic and celebrity detection."""

import logging
from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Celebrity, Post, PostAnalysis

logger = logging.getLogger(__name__)


class TrendingDetector:
    """
    Detect trending celebrities and topics.

    Analyzes recent viral posts to identify:
    - Celebrities with most viral content
    - Trending topics/themes
    - Emerging celebrities (new viral accounts)
    """

    def __init__(self, lookback_hours: int = 72):
        self.lookback_hours = lookback_hours

    async def get_trending_celebrities(
        self,
        db: AsyncSession,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get celebrities with most viral posts recently.

        Args:
            db: Database session
            limit: Max celebrities to return

        Returns:
            List of trending celebrity data
        """
        cutoff = datetime.utcnow() - timedelta(hours=self.lookback_hours)

        # Query celebrities with viral posts in the lookback period
        query = (
            select(
                Celebrity,
                func.count(Post.id).label("viral_count"),
                func.sum(Post.like_count).label("total_likes"),
                func.sum(Post.comment_count).label("total_comments"),
                func.avg(Post.viral_score).label("avg_viral_score"),
            )
            .join(Post, Celebrity.id == Post.celebrity_id)
            .where(Post.is_viral == True)
            .where(Post.scraped_at >= cutoff)
            .group_by(Celebrity.id)
            .order_by(func.count(Post.id).desc())
            .limit(limit)
        )

        result = await db.execute(query)
        rows = result.all()

        trending = []
        for row in rows:
            celeb = row[0]
            trending.append({
                "id": str(celeb.id),
                "username": celeb.instagram_username,
                "full_name": celeb.full_name,
                "category": celeb.category,
                "follower_count": celeb.follower_count,
                "viral_posts": row.viral_count,
                "total_likes": row.total_likes or 0,
                "total_comments": row.total_comments or 0,
                "avg_viral_score": round(row.avg_viral_score or 0, 2),
            })

        return trending

    async def get_hot_posts(
        self,
        db: AsyncSession,
        limit: int = 20,
        min_viral_score: float = 50.0,
    ) -> List[Dict[str, Any]]:
        """
        Get the hottest viral posts right now.

        Args:
            db: Database session
            limit: Max posts to return
            min_viral_score: Minimum viral score

        Returns:
            List of hot post data
        """
        cutoff = datetime.utcnow() - timedelta(hours=self.lookback_hours)

        query = (
            select(Post, Celebrity)
            .join(Celebrity, Post.celebrity_id == Celebrity.id)
            .where(Post.is_viral == True)
            .where(Post.scraped_at >= cutoff)
            .where(Post.viral_score >= min_viral_score)
            .order_by(Post.viral_score.desc())
            .limit(limit)
        )

        result = await db.execute(query)
        rows = result.all()

        hot_posts = []
        for post, celeb in rows:
            hot_posts.append({
                "id": str(post.id),
                "shortcode": post.shortcode,
                "celebrity": celeb.instagram_username,
                "celebrity_name": celeb.full_name,
                "likes": post.like_count,
                "comments": post.comment_count,
                "viral_score": post.viral_score,
                "posted_at": post.posted_at.isoformat() if post.posted_at else None,
                "is_analyzed": post.is_analyzed,
                "is_processed": post.is_processed,
            })

        return hot_posts

    async def get_unprocessed_viral_posts(
        self,
        db: AsyncSession,
        limit: int = 10,
    ) -> List[Post]:
        """
        Get viral posts that haven't been processed yet.

        Args:
            db: Database session
            limit: Max posts to return

        Returns:
            List of Post objects
        """
        query = (
            select(Post)
            .where(Post.is_viral == True)
            .where(Post.is_processed == False)
            .order_by(Post.viral_score.desc())
            .limit(limit)
        )

        result = await db.execute(query)
        return result.scalars().all()

    async def get_unanalyzed_viral_posts(
        self,
        db: AsyncSession,
        limit: int = 10,
    ) -> List[Post]:
        """
        Get viral posts that haven't been analyzed yet.

        Args:
            db: Database session
            limit: Max posts to return

        Returns:
            List of Post objects
        """
        query = (
            select(Post)
            .where(Post.is_viral == True)
            .where(Post.is_analyzed == False)
            .order_by(Post.viral_score.desc())
            .limit(limit)
        )

        result = await db.execute(query)
        return result.scalars().all()

    async def calculate_trending_score(
        self,
        db: AsyncSession,
        celebrity_id: UUID,
    ) -> float:
        """
        Calculate a trending score for a celebrity.

        Args:
            db: Database session
            celebrity_id: Celebrity UUID

        Returns:
            Trending score (0-100)
        """
        cutoff = datetime.utcnow() - timedelta(hours=self.lookback_hours)

        # Get recent viral posts
        query = (
            select(
                func.count(Post.id),
                func.sum(Post.viral_score),
            )
            .where(Post.celebrity_id == celebrity_id)
            .where(Post.is_viral == True)
            .where(Post.scraped_at >= cutoff)
        )

        result = await db.execute(query)
        row = result.one()

        viral_count = row[0] or 0
        total_score = row[1] or 0

        if viral_count == 0:
            return 0.0

        # Score based on number of viral posts and their scores
        post_score = min(viral_count * 10, 50)  # Max 50 points for 5+ viral posts
        avg_viral_score = total_score / viral_count
        quality_score = min(avg_viral_score / 2, 50)  # Max 50 points for 100 avg score

        return round(post_score + quality_score, 2)
