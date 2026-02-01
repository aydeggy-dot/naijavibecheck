"""Rate limiting for Instagram API requests."""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Optional

import redis.asyncio as redis

from app.config import settings


class RateLimiter:
    """
    Rate limiter for Instagram scraping requests.

    Features:
    - Per-account request limits
    - Exponential backoff on rate limit errors
    - Redis-backed for distributed operation
    """

    def __init__(
        self,
        max_requests_per_hour: int = 100,
        max_requests_per_day: int = 500,
    ):
        self.max_per_hour = max_requests_per_hour
        self.max_per_day = max_requests_per_day
        self.redis: Optional[redis.Redis] = None
        self._backoff_until: Optional[datetime] = None
        self._backoff_seconds = 60  # Initial backoff

    async def initialize(self):
        """Initialize Redis connection."""
        self.redis = redis.from_url(settings.redis_url)

    async def close(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()

    async def wait_if_needed(self, account_id: str = "default"):
        """
        Wait if we've hit rate limits.

        Args:
            account_id: The scraper account identifier
        """
        # Check global backoff
        if self._backoff_until and datetime.utcnow() < self._backoff_until:
            wait_seconds = (self._backoff_until - datetime.utcnow()).total_seconds()
            await asyncio.sleep(wait_seconds)
            self._backoff_until = None
            self._backoff_seconds = 60  # Reset backoff

        # Check per-account limits if Redis is available
        if self.redis:
            hour_key = f"rate:{account_id}:hour:{datetime.utcnow().strftime('%Y%m%d%H')}"
            day_key = f"rate:{account_id}:day:{datetime.utcnow().strftime('%Y%m%d')}"

            hour_count = await self.redis.get(hour_key)
            day_count = await self.redis.get(day_key)

            hour_count = int(hour_count) if hour_count else 0
            day_count = int(day_count) if day_count else 0

            # If we've hit daily limit, wait until tomorrow
            if day_count >= self.max_per_day:
                tomorrow = datetime.utcnow().replace(
                    hour=0, minute=0, second=0
                ) + timedelta(days=1)
                wait_seconds = (tomorrow - datetime.utcnow()).total_seconds()
                raise RateLimitExceeded(
                    f"Daily limit reached. Wait {wait_seconds:.0f} seconds."
                )

            # If we've hit hourly limit, wait until next hour
            if hour_count >= self.max_per_hour:
                next_hour = datetime.utcnow().replace(
                    minute=0, second=0
                ) + timedelta(hours=1)
                wait_seconds = (next_hour - datetime.utcnow()).total_seconds()
                await asyncio.sleep(min(wait_seconds, 300))  # Max 5 min wait

    async def record_request(self, account_id: str = "default"):
        """Record a request for rate limiting."""
        if self.redis:
            hour_key = f"rate:{account_id}:hour:{datetime.utcnow().strftime('%Y%m%d%H')}"
            day_key = f"rate:{account_id}:day:{datetime.utcnow().strftime('%Y%m%d')}"

            pipe = self.redis.pipeline()
            pipe.incr(hour_key)
            pipe.expire(hour_key, 3600)  # 1 hour
            pipe.incr(day_key)
            pipe.expire(day_key, 86400)  # 24 hours
            await pipe.execute()

    async def backoff(self):
        """Apply exponential backoff after a rate limit error."""
        self._backoff_until = datetime.utcnow() + timedelta(seconds=self._backoff_seconds)
        self._backoff_seconds = min(self._backoff_seconds * 2, 3600)  # Max 1 hour

    async def get_stats(self, account_id: str = "default") -> dict:
        """Get current rate limit stats for an account."""
        if not self.redis:
            return {"hour": 0, "day": 0}

        hour_key = f"rate:{account_id}:hour:{datetime.utcnow().strftime('%Y%m%d%H')}"
        day_key = f"rate:{account_id}:day:{datetime.utcnow().strftime('%Y%m%d')}"

        hour_count = await self.redis.get(hour_key)
        day_count = await self.redis.get(day_key)

        return {
            "hour": int(hour_count) if hour_count else 0,
            "day": int(day_count) if day_count else 0,
            "hour_limit": self.max_per_hour,
            "day_limit": self.max_per_day,
        }


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""

    pass
