"""Comment selection algorithms for top positive/negative comments."""

import logging
from typing import Dict, List, Tuple, Any

logger = logging.getLogger(__name__)


class CommentSelector:
    """
    Select the best comments for content generation.

    Criteria for selection:
    - Sentiment score (positive or negative extremes)
    - Toxicity level (for negative selection)
    - Comment length (not too short, not too long)
    - Like count (popular comments are more interesting)
    - Uniqueness (avoid similar comments)
    """

    def __init__(
        self,
        min_length: int = 10,
        max_length: int = 300,
        ideal_length: int = 100,
    ):
        self.min_length = min_length
        self.max_length = max_length
        self.ideal_length = ideal_length

    def select_top_comments(
        self,
        analyzed_comments: List[Dict[str, Any]],
        top_n: int = 3,
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Select top positive and negative comments.

        Args:
            analyzed_comments: Comments with sentiment analysis
            top_n: Number of top comments to select for each category

        Returns:
            Tuple of (top_positive, top_negative)
        """
        # Filter and score comments
        scored_positive = []
        scored_negative = []

        for comment in analyzed_comments:
            text = comment.get("text", "")

            # Skip very short or very long comments
            if len(text) < self.min_length or len(text) > self.max_length:
                continue

            score = self._calculate_selection_score(comment)
            comment["selection_score"] = score

            sentiment = comment.get("sentiment", "neutral")
            sentiment_score = comment.get("sentiment_score", 0)
            toxicity = comment.get("toxicity_score", 0)

            # Categorize based on sentiment and toxicity
            if sentiment == "positive" and toxicity < 0.3:
                scored_positive.append(comment)
            elif sentiment == "negative" or toxicity > 0.5:
                scored_negative.append(comment)

        # Sort by selection score
        scored_positive.sort(key=lambda x: x["selection_score"], reverse=True)
        scored_negative.sort(key=lambda x: x["selection_score"], reverse=True)

        # Select diverse top comments
        top_positive = self._select_diverse(scored_positive, top_n)
        top_negative = self._select_diverse(scored_negative, top_n)

        return top_positive, top_negative

    def _calculate_selection_score(self, comment: Dict[str, Any]) -> float:
        """
        Calculate a selection score for a comment.

        Higher score = better candidate for selection.
        """
        score = 0.0
        text = comment.get("text", "")

        # Sentiment intensity (0-30 points)
        sentiment_score = abs(comment.get("sentiment_score", 0))
        score += sentiment_score * 30

        # Toxicity intensity for negative comments (0-20 points)
        toxicity = comment.get("toxicity_score", 0)
        if comment.get("sentiment") == "negative":
            score += toxicity * 20

        # Length preference (0-20 points)
        length = len(text)
        if length >= self.min_length:
            # Prefer comments closer to ideal length
            length_score = 20 - abs(length - self.ideal_length) / 10
            score += max(length_score, 0)

        # Like count bonus (0-20 points)
        likes = comment.get("like_count", 0)
        like_score = min(likes / 50, 20)  # Max 20 points at 1000 likes
        score += like_score

        # Notable flag bonus (10 points)
        if comment.get("is_notable"):
            score += 10

        # Emotion diversity bonus (0-10 points)
        emotions = comment.get("emotion_tags", [])
        if emotions:
            score += min(len(emotions) * 2, 10)

        return score

    def _select_diverse(
        self,
        comments: List[Dict[str, Any]],
        top_n: int,
    ) -> List[Dict[str, Any]]:
        """
        Select diverse comments (avoid similar ones).

        Args:
            comments: Sorted comments by score
            top_n: Number to select

        Returns:
            Diverse selection of comments
        """
        if len(comments) <= top_n:
            return comments

        selected = []
        selected_texts = []

        for comment in comments:
            if len(selected) >= top_n:
                break

            text = comment.get("text", "").lower()

            # Check similarity with already selected comments
            is_similar = False
            for existing_text in selected_texts:
                similarity = self._text_similarity(text, existing_text)
                if similarity > 0.6:  # 60% similarity threshold
                    is_similar = True
                    break

            if not is_similar:
                selected.append(comment)
                selected_texts.append(text)

        return selected

    def _text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate simple text similarity using word overlap.

        Returns value between 0 and 1.
        """
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    def get_comment_highlights(
        self,
        top_positive: List[Dict],
        top_negative: List[Dict],
    ) -> Dict[str, Any]:
        """
        Get highlight statistics from selected comments.

        Args:
            top_positive: Top positive comments
            top_negative: Top negative comments

        Returns:
            Highlight statistics
        """
        return {
            "positive": {
                "count": len(top_positive),
                "avg_sentiment": (
                    sum(c.get("sentiment_score", 0) for c in top_positive) / len(top_positive)
                    if top_positive else 0
                ),
                "avg_likes": (
                    sum(c.get("like_count", 0) for c in top_positive) / len(top_positive)
                    if top_positive else 0
                ),
                "emotions": self._aggregate_emotions(top_positive),
            },
            "negative": {
                "count": len(top_negative),
                "avg_toxicity": (
                    sum(c.get("toxicity_score", 0) for c in top_negative) / len(top_negative)
                    if top_negative else 0
                ),
                "avg_likes": (
                    sum(c.get("like_count", 0) for c in top_negative) / len(top_negative)
                    if top_negative else 0
                ),
                "emotions": self._aggregate_emotions(top_negative),
            },
        }

    def _aggregate_emotions(self, comments: List[Dict]) -> Dict[str, int]:
        """Aggregate emotion tags from comments."""
        emotions = {}
        for comment in comments:
            for emotion in comment.get("emotion_tags", []):
                emotions[emotion] = emotions.get(emotion, 0) + 1
        return emotions
