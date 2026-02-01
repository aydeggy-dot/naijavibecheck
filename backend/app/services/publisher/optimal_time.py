"""Optimal posting time calculator."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import GeneratedContent, OurEngagement

logger = logging.getLogger(__name__)

# Lagos timezone
LAGOS_TZ = ZoneInfo("Africa/Lagos")


class OptimalTimeCalculator:
    """
    Calculate optimal posting times based on engagement data.

    Factors considered:
    - Historical engagement by hour/day
    - Nigerian audience active times
    - Content type performance
    - Default best practices
    """

    # Default optimal hours for Nigerian audience (Lagos time)
    # Based on typical social media usage patterns
    DEFAULT_OPTIMAL_HOURS = {
        0: [8, 12, 18, 20],   # Monday
        1: [8, 12, 18, 20],   # Tuesday
        2: [8, 12, 18, 20],   # Wednesday
        3: [8, 12, 18, 21],   # Thursday
        4: [9, 13, 17, 21],   # Friday
        5: [10, 14, 18, 21],  # Saturday
        6: [10, 14, 17, 20],  # Sunday
    }

    # Peak engagement windows
    PEAK_WINDOWS = [
        (7, 9),    # Morning commute
        (12, 14),  # Lunch break
        (18, 21),  # Evening prime time
    ]

    def __init__(self):
        self.engagement_data: Dict[str, float] = {}

    async def get_optimal_time(
        self,
        db: AsyncSession,
        content_type: str = "carousel",
        target_date: datetime = None,
    ) -> datetime:
        """
        Get the optimal posting time.

        Args:
            db: Database session
            content_type: Type of content
            target_date: Target date (default: today or tomorrow)

        Returns:
            Optimal datetime in UTC
        """
        # Default to next available slot
        if not target_date:
            target_date = datetime.now(LAGOS_TZ)

        # If it's late in the day, schedule for tomorrow
        if target_date.hour >= 20:
            target_date = target_date + timedelta(days=1)

        day_of_week = target_date.weekday()

        # Try to get learned optimal times
        learned_hour = await self._get_learned_optimal_hour(db, day_of_week, content_type)

        if learned_hour is not None:
            optimal_hour = learned_hour
        else:
            # Use default optimal hours
            optimal_hours = self.DEFAULT_OPTIMAL_HOURS.get(day_of_week, [12, 18])
            optimal_hour = self._select_next_available_hour(target_date, optimal_hours)

        # Create datetime in Lagos timezone
        optimal_time = target_date.replace(
            hour=optimal_hour,
            minute=0,
            second=0,
            microsecond=0,
        )

        # If the time has passed, move to next day
        if optimal_time <= datetime.now(LAGOS_TZ):
            optimal_time = optimal_time + timedelta(days=1)

        # Convert to UTC for storage
        return optimal_time.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)

    async def _get_learned_optimal_hour(
        self,
        db: AsyncSession,
        day_of_week: int,
        content_type: str,
    ) -> Optional[int]:
        """
        Get optimal hour from historical engagement data.

        Returns the hour with highest average engagement for the given day.
        """
        from app.models import ContentPerformance

        # Query engagement by hour for this day of week
        result = await db.execute(
            select(
                ContentPerformance.post_hour,
                func.avg(ContentPerformance.engagement_score).label("avg_engagement"),
            )
            .where(ContentPerformance.post_day_of_week == day_of_week)
            .where(ContentPerformance.content_type == content_type)
            .group_by(ContentPerformance.post_hour)
            .having(func.count() >= 3)  # Need at least 3 data points
            .order_by(func.avg(ContentPerformance.engagement_score).desc())
            .limit(1)
        )

        row = result.first()
        if row and row.avg_engagement:
            return row.post_hour

        return None

    def _select_next_available_hour(
        self,
        target_date: datetime,
        optimal_hours: List[int],
    ) -> int:
        """Select the next available optimal hour."""
        current_hour = target_date.hour

        # Find next optimal hour today
        for hour in optimal_hours:
            if hour > current_hour:
                return hour

        # If all hours passed, return first optimal hour (for tomorrow)
        return optimal_hours[0]

    def is_peak_time(self, dt: datetime = None) -> bool:
        """Check if the given time is during peak engagement window."""
        if dt is None:
            dt = datetime.now(LAGOS_TZ)
        else:
            dt = dt.astimezone(LAGOS_TZ)

        hour = dt.hour
        for start, end in self.PEAK_WINDOWS:
            if start <= hour <= end:
                return True
        return False

    async def get_schedule_suggestions(
        self,
        db: AsyncSession,
        count: int = 5,
        start_date: datetime = None,
    ) -> List[Dict[str, Any]]:
        """
        Get multiple schedule suggestions.

        Args:
            db: Database session
            count: Number of suggestions
            start_date: Starting date

        Returns:
            List of suggested times with confidence scores
        """
        if start_date is None:
            start_date = datetime.now(LAGOS_TZ)

        suggestions = []
        current_date = start_date

        while len(suggestions) < count:
            day_of_week = current_date.weekday()
            optimal_hours = self.DEFAULT_OPTIMAL_HOURS.get(day_of_week, [12, 18])

            for hour in optimal_hours:
                if len(suggestions) >= count:
                    break

                suggested_time = current_date.replace(
                    hour=hour,
                    minute=0,
                    second=0,
                    microsecond=0,
                )

                # Skip if in the past
                if suggested_time <= datetime.now(LAGOS_TZ):
                    continue

                # Calculate confidence score
                confidence = self._calculate_confidence(hour, day_of_week)

                suggestions.append({
                    "datetime": suggested_time.astimezone(ZoneInfo("UTC")).replace(tzinfo=None),
                    "datetime_lagos": suggested_time.isoformat(),
                    "day": suggested_time.strftime("%A"),
                    "time": suggested_time.strftime("%I:%M %p"),
                    "confidence": confidence,
                    "is_peak": self.is_peak_time(suggested_time),
                })

            current_date = current_date + timedelta(days=1)

        return suggestions

    def _calculate_confidence(self, hour: int, day_of_week: int) -> float:
        """Calculate confidence score for a time slot."""
        confidence = 0.5  # Base confidence

        # Peak time bonus
        for start, end in self.PEAK_WINDOWS:
            if start <= hour <= end:
                confidence += 0.3
                break

        # Weekend adjustment
        if day_of_week >= 5:  # Saturday or Sunday
            if 10 <= hour <= 14:
                confidence += 0.1
            elif 18 <= hour <= 21:
                confidence += 0.2

        # Weekday adjustment
        else:
            if 18 <= hour <= 21:
                confidence += 0.2

        return min(confidence, 1.0)

    async def record_post_performance(
        self,
        db: AsyncSession,
        content_id: str,
        engagement_score: float,
    ):
        """
        Record posting performance for learning.

        Called after engagement is tracked to improve future predictions.
        """
        from app.models import ContentPerformance, GeneratedContent

        content = await db.get(GeneratedContent, content_id)
        if not content or not content.published_at:
            return

        published_lagos = content.published_at.replace(
            tzinfo=ZoneInfo("UTC")
        ).astimezone(LAGOS_TZ)

        performance = ContentPerformance(
            generated_content_id=content.id,
            content_type=content.content_type,
            post_hour=published_lagos.hour,
            post_day_of_week=published_lagos.weekday(),
            engagement_score=engagement_score,
        )

        db.add(performance)
        await db.flush()
