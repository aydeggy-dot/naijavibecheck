"""Tests for publishing services."""

import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.services.publisher.optimal_time import OptimalTimeCalculator, LAGOS_TZ
from app.services.publisher.instagram_publisher import MockInstagramPublisher


class TestOptimalTimeCalculator:
    """Tests for optimal time calculation."""

    def setup_method(self):
        self.calculator = OptimalTimeCalculator()

    def test_default_optimal_hours_exist(self):
        """Test that default optimal hours are defined."""
        assert len(self.calculator.DEFAULT_OPTIMAL_HOURS) == 7  # All days
        for day in range(7):
            assert day in self.calculator.DEFAULT_OPTIMAL_HOURS
            assert len(self.calculator.DEFAULT_OPTIMAL_HOURS[day]) > 0

    def test_is_peak_time_morning(self):
        """Test peak time detection for morning."""
        morning = datetime(2024, 1, 15, 8, 30, tzinfo=LAGOS_TZ)
        assert self.calculator.is_peak_time(morning)

    def test_is_peak_time_lunch(self):
        """Test peak time detection for lunch."""
        lunch = datetime(2024, 1, 15, 13, 0, tzinfo=LAGOS_TZ)
        assert self.calculator.is_peak_time(lunch)

    def test_is_peak_time_evening(self):
        """Test peak time detection for evening."""
        evening = datetime(2024, 1, 15, 19, 30, tzinfo=LAGOS_TZ)
        assert self.calculator.is_peak_time(evening)

    def test_is_not_peak_time(self):
        """Test non-peak time detection."""
        offpeak = datetime(2024, 1, 15, 3, 0, tzinfo=LAGOS_TZ)
        assert not self.calculator.is_peak_time(offpeak)

    def test_confidence_calculation(self):
        """Test confidence score calculation."""
        # Peak evening hour on weekday
        confidence = self.calculator._calculate_confidence(19, 1)  # Tuesday 7 PM
        assert confidence > 0.5

        # Off-peak hour
        confidence_low = self.calculator._calculate_confidence(3, 1)  # Tuesday 3 AM
        assert confidence_low <= confidence

    def test_select_next_available_hour(self):
        """Test selecting next available optimal hour."""
        optimal_hours = [8, 12, 18, 20]

        # At 10 AM, should select 12
        target = datetime(2024, 1, 15, 10, 0)
        assert self.calculator._select_next_available_hour(target, optimal_hours) == 12

        # At 19 PM, should select 20
        target = datetime(2024, 1, 15, 19, 0)
        assert self.calculator._select_next_available_hour(target, optimal_hours) == 20

        # At 21 PM (all passed), should select first (8)
        target = datetime(2024, 1, 15, 21, 0)
        assert self.calculator._select_next_available_hour(target, optimal_hours) == 8


class TestMockInstagramPublisher:
    """Tests for mock Instagram publisher."""

    @pytest.fixture
    def publisher(self):
        return MockInstagramPublisher()

    @pytest.mark.asyncio
    async def test_initialize(self, publisher):
        """Test mock initialization."""
        result = await publisher.initialize()
        assert result is True
        assert publisher.logged_in is True

    @pytest.mark.asyncio
    async def test_publish_image(self, publisher):
        """Test mock image publishing."""
        await publisher.initialize()

        media_id = await publisher.publish_image(
            image_path="/path/to/image.png",
            caption="Test caption",
        )

        assert media_id is not None
        assert media_id.startswith("mock_")
        assert len(publisher.published_posts) == 1
        assert publisher.published_posts[0]["type"] == "image"

    @pytest.mark.asyncio
    async def test_publish_carousel(self, publisher):
        """Test mock carousel publishing."""
        await publisher.initialize()

        media_id = await publisher.publish_carousel(
            image_paths=["/path/to/img1.png", "/path/to/img2.png"],
            caption="Test carousel",
        )

        assert media_id is not None
        assert len(publisher.published_posts) == 1
        assert publisher.published_posts[0]["type"] == "carousel"

    @pytest.mark.asyncio
    async def test_get_media_insights(self, publisher):
        """Test mock insights retrieval."""
        await publisher.initialize()

        insights = await publisher.get_media_insights("mock_123")

        assert insights is not None
        assert "like_count" in insights
        assert "comment_count" in insights
        assert insights["like_count"] >= 100


class TestContentScheduler:
    """Tests for content scheduler (requires DB fixtures)."""

    # Note: These tests would need async DB fixtures
    # Placeholder for integration tests

    def test_placeholder(self):
        """Placeholder test."""
        assert True
