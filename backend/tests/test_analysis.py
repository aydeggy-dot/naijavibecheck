"""Tests for analysis services."""

import pytest
from datetime import datetime, timedelta

from app.services.analyzer.viral_scorer import ViralScorer
from app.services.analyzer.comment_selector import CommentSelector


class TestViralScorer:
    """Tests for viral scoring."""

    def setup_method(self):
        self.scorer = ViralScorer(
            min_likes=100_000,
            min_comments=25_000,
            max_age_days=3,
        )

    def test_is_viral_meets_thresholds(self):
        """Test post that meets viral thresholds."""
        assert self.scorer.is_viral(
            likes=150_000,
            comments=30_000,
            posted_at=datetime.utcnow() - timedelta(hours=12),
        )

    def test_is_viral_below_likes(self):
        """Test post below likes threshold."""
        assert not self.scorer.is_viral(
            likes=50_000,
            comments=30_000,
        )

    def test_is_viral_below_comments(self):
        """Test post below comments threshold."""
        assert not self.scorer.is_viral(
            likes=150_000,
            comments=10_000,
        )

    def test_is_viral_too_old(self):
        """Test post that's too old."""
        assert not self.scorer.is_viral(
            likes=150_000,
            comments=30_000,
            posted_at=datetime.utcnow() - timedelta(days=5),
        )

    def test_calculate_viral_score(self):
        """Test viral score calculation."""
        score = self.scorer.calculate_viral_score(
            likes=200_000,
            comments=50_000,
        )
        assert score > 0
        assert score <= 100

    def test_viral_score_increases_with_engagement(self):
        """Test that higher engagement gives higher score."""
        low_score = self.scorer.calculate_viral_score(
            likes=100_000,
            comments=25_000,
        )
        high_score = self.scorer.calculate_viral_score(
            likes=500_000,
            comments=100_000,
        )
        assert high_score > low_score

    def test_controversy_bonus(self):
        """Test that high comment ratio adds controversy bonus."""
        # Same likes, different comment ratios
        low_controversy = self.scorer.calculate_viral_score(
            likes=200_000,
            comments=20_000,  # 10% ratio
        )
        high_controversy = self.scorer.calculate_viral_score(
            likes=200_000,
            comments=100_000,  # 50% ratio
        )
        assert high_controversy > low_controversy

    def test_get_viral_tier(self):
        """Test viral tier classification."""
        assert self.scorer.get_viral_tier(90) == "mega_viral"
        assert self.scorer.get_viral_tier(70) == "viral"
        assert self.scorer.get_viral_tier(50) == "trending"
        assert self.scorer.get_viral_tier(30) == "popular"
        assert self.scorer.get_viral_tier(10) == "normal"

    def test_analyze_post(self):
        """Test full post analysis."""
        result = self.scorer.analyze_post(
            post_data={
                "like_count": 200_000,
                "comment_count": 50_000,
                "posted_at": datetime.utcnow() - timedelta(hours=6),
            },
            follower_count=5_000_000,
        )

        assert "viral_score" in result
        assert "is_viral" in result
        assert "tier" in result
        assert "engagement_rate" in result
        assert "controversy_level" in result
        assert result["is_viral"] == True


class TestCommentSelector:
    """Tests for comment selection."""

    def setup_method(self):
        self.selector = CommentSelector(
            min_length=10,
            max_length=300,
            ideal_length=100,
        )

    def test_select_top_comments(self):
        """Test selecting top positive and negative comments."""
        comments = [
            {
                "id": "1",
                "text": "This is amazing! Love it so much! 🔥",
                "sentiment": "positive",
                "sentiment_score": 0.9,
                "toxicity_score": 0.1,
                "like_count": 50,
            },
            {
                "id": "2",
                "text": "Beautiful work, keep it up queen!",
                "sentiment": "positive",
                "sentiment_score": 0.8,
                "toxicity_score": 0.0,
                "like_count": 30,
            },
            {
                "id": "3",
                "text": "This is terrible and fake",
                "sentiment": "negative",
                "sentiment_score": -0.7,
                "toxicity_score": 0.6,
                "like_count": 20,
            },
            {
                "id": "4",
                "text": "Worst thing I've ever seen, disgusting",
                "sentiment": "negative",
                "sentiment_score": -0.9,
                "toxicity_score": 0.8,
                "like_count": 15,
            },
        ]

        top_positive, top_negative = self.selector.select_top_comments(comments, top_n=2)

        assert len(top_positive) <= 2
        assert len(top_negative) <= 2
        assert all(c["sentiment"] == "positive" for c in top_positive)

    def test_filters_short_comments(self):
        """Test that very short comments are filtered."""
        comments = [
            {
                "id": "1",
                "text": "Nice",  # Too short
                "sentiment": "positive",
                "sentiment_score": 0.5,
                "toxicity_score": 0.0,
                "like_count": 100,
            },
            {
                "id": "2",
                "text": "This is a much longer comment with more detail",
                "sentiment": "positive",
                "sentiment_score": 0.5,
                "toxicity_score": 0.0,
                "like_count": 10,
            },
        ]

        top_positive, _ = self.selector.select_top_comments(comments, top_n=2)

        # Short comment should be filtered
        assert len(top_positive) == 1
        assert top_positive[0]["id"] == "2"

    def test_diversity_selection(self):
        """Test that similar comments aren't selected together."""
        comments = [
            {
                "id": "1",
                "text": "I love this so much, amazing work!",
                "sentiment": "positive",
                "sentiment_score": 0.9,
                "toxicity_score": 0.0,
                "like_count": 50,
            },
            {
                "id": "2",
                "text": "I love this so much, amazing job!",  # Very similar
                "sentiment": "positive",
                "sentiment_score": 0.9,
                "toxicity_score": 0.0,
                "like_count": 40,
            },
            {
                "id": "3",
                "text": "Beautiful and inspiring content",  # Different
                "sentiment": "positive",
                "sentiment_score": 0.8,
                "toxicity_score": 0.0,
                "like_count": 30,
            },
        ]

        top_positive, _ = self.selector.select_top_comments(comments, top_n=2)

        # Should prefer diverse comments
        ids = [c["id"] for c in top_positive]
        # Comment 1 and 3 should be selected (diverse), not 1 and 2 (similar)
        assert "1" in ids
        assert "3" in ids

    def test_get_comment_highlights(self):
        """Test highlight statistics generation."""
        top_positive = [
            {"sentiment_score": 0.9, "like_count": 50, "emotion_tags": ["happy", "supportive"]},
            {"sentiment_score": 0.8, "like_count": 30, "emotion_tags": ["happy"]},
        ]
        top_negative = [
            {"toxicity_score": 0.8, "like_count": 20, "emotion_tags": ["angry"]},
        ]

        highlights = self.selector.get_comment_highlights(top_positive, top_negative)

        assert "positive" in highlights
        assert "negative" in highlights
        assert highlights["positive"]["count"] == 2
        assert highlights["negative"]["count"] == 1
        assert highlights["positive"]["avg_sentiment"] == 0.85
