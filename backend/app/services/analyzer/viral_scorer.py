"""Viral score calculation for Instagram posts."""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class ViralScorer:
    """
    Calculate viral scores for Instagram posts.

    Factors considered:
    - Raw engagement (likes, comments)
    - Engagement velocity (engagement / post age)
    - Comment-to-like ratio (controversy indicator)
    - Celebrity follower count (relative engagement)
    """

    def __init__(
        self,
        min_likes: int = None,
        min_comments: int = None,
        max_age_days: int = None,
    ):
        self.min_likes = min_likes or settings.min_post_likes
        self.min_comments = min_comments or settings.min_post_comments
        self.max_age_days = max_age_days or settings.max_post_age_days

    def calculate_viral_score(
        self,
        likes: int,
        comments: int,
        posted_at: Optional[datetime] = None,
        follower_count: Optional[int] = None,
    ) -> float:
        """
        Calculate a viral score from 0-100.

        Args:
            likes: Number of likes
            comments: Number of comments
            posted_at: When the post was created
            follower_count: Celebrity's follower count

        Returns:
            Viral score (0-100)
        """
        score = 0.0

        # Base engagement score (0-40 points)
        likes_score = min((likes / 500_000) * 20, 20)  # Max 20 points at 500K likes
        comments_score = min((comments / 50_000) * 20, 20)  # Max 20 points at 50K comments
        score += likes_score + comments_score

        # Controversy bonus (0-20 points)
        # High comment-to-like ratio indicates heated discussion
        if likes > 0:
            comment_ratio = comments / likes
            controversy_score = min(comment_ratio * 40, 20)
            score += controversy_score

        # Velocity bonus (0-20 points)
        # Faster engagement = more viral
        if posted_at:
            age_hours = max((datetime.utcnow() - posted_at).total_seconds() / 3600, 1)
            engagement_per_hour = (likes + comments) / age_hours
            velocity_score = min((engagement_per_hour / 10_000) * 20, 20)
            score += velocity_score

        # Relative engagement bonus (0-20 points)
        # High engagement relative to follower count
        if follower_count and follower_count > 0:
            engagement_rate = (likes + comments) / follower_count
            relative_score = min(engagement_rate * 200, 20)  # 10% engagement = 20 points
            score += relative_score

        return min(score, 100)

    def is_viral(
        self,
        likes: int,
        comments: int,
        posted_at: Optional[datetime] = None,
    ) -> bool:
        """
        Check if a post meets viral thresholds.

        Args:
            likes: Number of likes
            comments: Number of comments
            posted_at: When the post was created

        Returns:
            True if post is viral
        """
        # Check minimum engagement
        if likes < self.min_likes or comments < self.min_comments:
            return False

        # Check age
        if posted_at:
            age = datetime.utcnow() - posted_at
            if age > timedelta(days=self.max_age_days):
                return False

        return True

    def get_viral_tier(self, score: float) -> str:
        """
        Get the viral tier based on score.

        Args:
            score: Viral score (0-100)

        Returns:
            Tier name
        """
        if score >= 80:
            return "mega_viral"
        elif score >= 60:
            return "viral"
        elif score >= 40:
            return "trending"
        elif score >= 20:
            return "popular"
        else:
            return "normal"

    def analyze_post(
        self,
        post_data: Dict[str, Any],
        follower_count: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Full viral analysis for a post.

        Args:
            post_data: Post data dict with likes, comments, posted_at
            follower_count: Celebrity's follower count

        Returns:
            Analysis results dict
        """
        likes = post_data.get("like_count", 0) or 0
        comments = post_data.get("comment_count", 0) or 0
        posted_at = post_data.get("posted_at")

        score = self.calculate_viral_score(
            likes=likes,
            comments=comments,
            posted_at=posted_at,
            follower_count=follower_count,
        )

        is_viral = self.is_viral(likes, comments, posted_at)
        tier = self.get_viral_tier(score)

        # Calculate engagement rate
        engagement_rate = None
        if follower_count and follower_count > 0:
            engagement_rate = ((likes + comments) / follower_count) * 100

        # Calculate controversy indicator
        controversy = "low"
        if likes > 0:
            ratio = comments / likes
            if ratio > 0.5:
                controversy = "high"
            elif ratio > 0.25:
                controversy = "medium"

        return {
            "viral_score": round(score, 2),
            "is_viral": is_viral,
            "tier": tier,
            "engagement_rate": round(engagement_rate, 4) if engagement_rate else None,
            "controversy_level": controversy,
            "meets_thresholds": {
                "likes": likes >= self.min_likes,
                "comments": comments >= self.min_comments,
                "age": self._check_age(posted_at),
            },
        }

    def _check_age(self, posted_at: Optional[datetime]) -> bool:
        """Check if post is within age threshold."""
        if not posted_at:
            return True
        age = datetime.utcnow() - posted_at
        return age <= timedelta(days=self.max_age_days)
