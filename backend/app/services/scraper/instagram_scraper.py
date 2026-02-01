"""Instagram scraper service using instaloader."""

import asyncio
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
from itertools import islice
import logging

import instaloader
from instaloader.exceptions import (
    LoginRequiredException,
    ProfileNotExistsException,
    ConnectionException,
    QueryReturnedBadRequestException,
)

from app.config import settings
from app.services.scraper.rate_limiter import RateLimiter, RateLimitExceeded
from app.services.scraper.browser_scraper import BrowserScraper

logger = logging.getLogger(__name__)


class InstagramScraperError(Exception):
    """Base exception for Instagram scraper errors."""
    pass


class InstagramLoginError(InstagramScraperError):
    """Login failed or authentication required."""
    pass


class InstagramRateLimitError(InstagramScraperError):
    """Instagram rate limit hit."""
    pass


class InstagramScraper:
    """
    Instagram scraping service using instaloader.

    Features:
    - No login required for public profiles and posts
    - Session persistence when login is available
    - Rate limiting integration
    - Random delays between requests (2-5 seconds)
    - Error handling with retry logic
    """

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        session_path: Optional[Path] = None,
    ):
        self.username = username or settings.instagram_scraper_username
        self.password = password or settings.instagram_scraper_password
        self.session_path = session_path or Path(settings.sessions_dir)

        self._loader: Optional[instaloader.Instaloader] = None
        self._initialized = False
        self._logged_in = False
        self._current_account_id: Optional[str] = None

        self.rate_limiter = RateLimiter(
            max_requests_per_hour=100,
            max_requests_per_day=settings.requests_per_account_per_day,
        )

        # Delay settings (seconds)
        self.min_delay = 2.0
        self.max_delay = 5.0

    async def initialize(self) -> bool:
        """
        Initialize the scraper.

        Works without login for public data (profiles, posts).
        Login only needed for comments and private profiles.

        Returns:
            True if initialization successful
        """
        if self._initialized and self._loader:
            return True

        await self.rate_limiter.initialize()

        # Create instaloader instance
        self._loader = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
        )

        self._current_account_id = self.username or "anonymous"
        self.session_path.mkdir(parents=True, exist_ok=True)

        # Try to load existing session
        if self.username:
            session_file = self.session_path / f"{self.username}_session"
            if session_file.exists():
                try:
                    logger.info(f"Loading existing session for @{self.username}")
                    self._loader.load_session_from_file(self.username, str(session_file))
                    self._logged_in = True
                    logger.info(f"Session loaded for @{self.username}")
                except Exception as e:
                    logger.warning(f"Failed to load session: {e}")

        self._initialized = True
        logger.info(f"Instagram scraper initialized (logged_in={self._logged_in})")
        return True

    async def close(self):
        """Clean up resources."""
        await self.rate_limiter.close()
        self._initialized = False
        self._loader = None

    async def _add_delay(self):
        """Add random delay between requests to avoid rate limiting."""
        delay = random.uniform(self.min_delay, self.max_delay)
        await asyncio.sleep(delay)

    async def _ensure_initialized(self):
        """Ensure scraper is initialized before making requests."""
        if not self._initialized or not self._loader:
            await self.initialize()

    async def _handle_error(self, error: Exception, context: str = ""):
        """Handle scraping errors with appropriate recovery actions."""
        error_str = str(error).lower()

        if isinstance(error, LoginRequiredException):
            logger.warning(f"Login required for {context}")
            raise InstagramLoginError(f"Login required: {error}")

        elif isinstance(error, ProfileNotExistsException):
            logger.warning(f"Profile not found in {context}")
            return None

        elif isinstance(error, ConnectionException):
            if "429" in error_str or "rate" in error_str:
                logger.warning(f"Rate limit hit during {context}")
                await self.rate_limiter.backoff()
                raise InstagramRateLimitError(f"Rate limited: {error}")
            else:
                logger.error(f"Connection error during {context}: {error}")
                raise InstagramScraperError(f"Connection error: {error}")

        elif isinstance(error, QueryReturnedBadRequestException):
            logger.warning(f"Bad request during {context}: {error}")
            await self.rate_limiter.backoff()
            raise InstagramRateLimitError(f"Bad request (possible rate limit): {error}")

        else:
            logger.error(f"Error during {context}: {error}")
            raise InstagramScraperError(f"Scraper error: {error}")

    async def get_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get profile information for a username.

        Works WITHOUT login for public profiles.

        Args:
            username: Instagram username (without @)

        Returns:
            Profile data dict or None if not found
        """
        await self._ensure_initialized()
        await self.rate_limiter.wait_if_needed(self._current_account_id or "default")

        try:
            await self._add_delay()

            profile = await asyncio.to_thread(
                instaloader.Profile.from_username,
                self._loader.context,
                username,
            )

            await self.rate_limiter.record_request(self._current_account_id or "default")

            logger.info(f"Fetched profile for @{username}")

            return {
                "user_id": str(profile.userid),
                "username": profile.username,
                "full_name": profile.full_name,
                "biography": profile.biography,
                "follower_count": profile.followers,
                "following_count": profile.followees,
                "post_count": profile.mediacount,
                "is_private": profile.is_private,
                "is_verified": profile.is_verified,
                "profile_pic_url": profile.profile_pic_url,
                "external_url": profile.external_url,
            }

        except ProfileNotExistsException:
            logger.warning(f"Profile @{username} not found")
            return None
        except Exception as e:
            await self._handle_error(e, f"get_profile({username})")
            return None

    async def get_recent_posts(
        self,
        username: str,
        max_posts: int = 20,
        max_age_days: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Get recent posts from a user.

        Works WITHOUT login for public profiles.

        Args:
            username: Instagram username
            max_posts: Maximum number of posts to fetch
            max_age_days: Only fetch posts newer than this

        Returns:
            List of post data dicts
        """
        await self._ensure_initialized()
        await self.rate_limiter.wait_if_needed(self._current_account_id or "default")

        try:
            await self._add_delay()

            profile = await asyncio.to_thread(
                instaloader.Profile.from_username,
                self._loader.context,
                username,
            )

            await self.rate_limiter.record_request(self._current_account_id or "default")

            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            posts = []

            def fetch_posts():
                post_iterator = profile.get_posts()
                for post in islice(post_iterator, max_posts * 2):  # Fetch extra in case some are filtered
                    if len(posts) >= max_posts:
                        break

                    # Filter by age
                    post_date = post.date_local.replace(tzinfo=None) if post.date_local else None
                    if post_date and post_date < cutoff_date:
                        continue

                    post_data = {
                        "post_id": str(post.mediaid),
                        "shortcode": post.shortcode,
                        "post_url": f"https://www.instagram.com/p/{post.shortcode}/",
                        "caption": post.caption,
                        "like_count": post.likes,
                        "comment_count": post.comments,
                        "posted_at": post.date_local,
                        "media_type": 2 if post.is_video else 1,  # 1=Photo, 2=Video
                        "thumbnail_url": post.url,
                    }
                    posts.append(post_data)
                return posts

            await asyncio.to_thread(fetch_posts)
            await self.rate_limiter.record_request(self._current_account_id or "default")

            logger.info(f"Fetched {len(posts)} recent posts for @{username}")
            return posts

        except ProfileNotExistsException:
            logger.warning(f"Profile @{username} not found")
            return []
        except Exception as e:
            await self._handle_error(e, f"get_recent_posts({username})")
            return []

    async def get_viral_posts(
        self,
        username: str,
        min_likes: Optional[int] = None,
        min_comments: Optional[int] = None,
        max_age_days: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get viral posts from a user that meet engagement thresholds.

        Args:
            username: Instagram username
            min_likes: Minimum like count (default from settings)
            min_comments: Minimum comment count (default from settings)
            max_age_days: Maximum post age (default from settings)

        Returns:
            List of viral post data dicts with viral_score
        """
        min_likes = min_likes or settings.min_post_likes
        min_comments = min_comments or settings.min_post_comments
        max_age_days = max_age_days or settings.max_post_age_days

        posts = await self.get_recent_posts(username, max_posts=30, max_age_days=max_age_days)

        viral_posts = [
            p for p in posts
            if p.get("like_count", 0) >= min_likes
            and p.get("comment_count", 0) >= min_comments
        ]

        for post in viral_posts:
            post["viral_score"] = self._calculate_viral_score(post)

        return sorted(viral_posts, key=lambda x: x["viral_score"], reverse=True)

    async def get_post_comments(
        self,
        shortcode: str,
        max_comments: int = 500,
        use_browser_fallback: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get comments from a post.

        Uses instaloader if logged in, falls back to browser scraping if not.

        Args:
            shortcode: Instagram post shortcode (e.g., "CxYZ123")
            max_comments: Maximum number of comments to fetch
            use_browser_fallback: If True, use browser scraping when login fails

        Returns:
            List of comment data dicts with anonymized usernames
        """
        await self._ensure_initialized()

        # Try instaloader first if logged in
        if self._logged_in:
            await self.rate_limiter.wait_if_needed(self._current_account_id or "default")

            try:
                await self._add_delay()

                post = await asyncio.to_thread(
                    instaloader.Post.from_shortcode,
                    self._loader.context,
                    shortcode,
                )

                await self.rate_limiter.record_request(self._current_account_id or "default")

                comments_data = []

                def fetch_comments():
                    for comment in islice(post.get_comments(), max_comments):
                        comment_dict = {
                            "comment_id": str(comment.id),
                            "username": comment.owner.username,
                            "username_anonymized": self.anonymize_username(comment.owner.username),
                            "text": comment.text,
                            "like_count": comment.likes_count if hasattr(comment, 'likes_count') else 0,
                            "commented_at": comment.created_at_utc,
                            "is_reply": False,  # Top-level comments
                            "parent_comment_id": None,
                        }
                        comments_data.append(comment_dict)
                    return comments_data

                await asyncio.to_thread(fetch_comments)
                await self.rate_limiter.record_request(self._current_account_id or "default")

                logger.info(f"Fetched {len(comments_data)} comments for post {shortcode} via instaloader")
                return comments_data

            except LoginRequiredException:
                logger.warning(f"Login required for comments on {shortcode}, trying browser fallback")
            except Exception as e:
                logger.warning(f"Instaloader error for {shortcode}: {e}, trying browser fallback")

        # Fallback to browser scraping
        if use_browser_fallback:
            logger.info(f"Using browser scraper for comments on {shortcode}")
            browser_scraper = BrowserScraper()
            try:
                comments = await browser_scraper.get_post_comments(shortcode, max_comments)
                logger.info(f"Fetched {len(comments)} comments for post {shortcode} via browser")
                return comments
            except Exception as e:
                logger.error(f"Browser scraper failed for {shortcode}: {e}")
            finally:
                await browser_scraper.close()

        logger.warning(f"Cannot fetch comments for {shortcode} - no login and browser fallback disabled/failed")
        return []

    async def get_post_by_shortcode(self, shortcode: str) -> Optional[Dict[str, Any]]:
        """
        Get a single post by its shortcode.

        Args:
            shortcode: Instagram post shortcode

        Returns:
            Post data dict or None if not found
        """
        await self._ensure_initialized()
        await self.rate_limiter.wait_if_needed(self._current_account_id or "default")

        try:
            await self._add_delay()

            post = await asyncio.to_thread(
                instaloader.Post.from_shortcode,
                self._loader.context,
                shortcode,
            )

            await self.rate_limiter.record_request(self._current_account_id or "default")

            return {
                "post_id": str(post.mediaid),
                "shortcode": post.shortcode,
                "post_url": f"https://www.instagram.com/p/{post.shortcode}/",
                "caption": post.caption,
                "like_count": post.likes,
                "comment_count": post.comments,
                "posted_at": post.date_local,
                "media_type": 2 if post.is_video else 1,
                "thumbnail_url": post.url,
                "user": {
                    "username": post.owner_username,
                    "full_name": post.owner_profile.full_name if post.owner_profile else None,
                }
            }

        except Exception as e:
            await self._handle_error(e, f"get_post_by_shortcode({shortcode})")
            return None

    def anonymize_username(self, username: str) -> str:
        """
        Anonymize username with asterisks for privacy.

        Example: 'johndoe123' -> 'joh***123'
        """
        if not username:
            return "***"

        if len(username) <= 4:
            return username[0] + "***"

        visible_start = len(username) // 3
        visible_end = len(username) // 3

        return (
            username[:visible_start]
            + "*" * (len(username) - visible_start - visible_end)
            + username[-visible_end:]
        )

    def _calculate_viral_score(self, post: Dict[str, Any]) -> float:
        """
        Calculate a viral score based on engagement metrics.

        Higher score = more viral
        """
        likes = post.get("like_count", 0)
        comments = post.get("comment_count", 0)

        # Base score from raw numbers
        base_score = (likes / 100_000) + (comments / 10_000)

        # Controversy bonus (high comment-to-like ratio = heated discussion)
        if likes > 0:
            controversy_bonus = min((comments / likes) * 10, 5)
        else:
            controversy_bonus = 0

        return min(base_score + controversy_bonus, 100)

    async def get_rate_limit_stats(self) -> Dict[str, Any]:
        """Get current rate limit statistics."""
        return await self.rate_limiter.get_stats(self._current_account_id or "default")

    def is_initialized(self) -> bool:
        """Check if scraper is initialized and ready."""
        return self._initialized and self._loader is not None

    def is_logged_in(self) -> bool:
        """Check if scraper has a valid login session."""
        return self._logged_in
