"""Instagram publisher service."""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from app.config import settings

logger = logging.getLogger(__name__)


class InstagramPublisher:
    """
    Publishes content to Instagram.

    Supports:
    - Single image posts
    - Carousel (album) posts
    - Reels (video posts)

    Uses instagrapi library for Instagram API access.
    """

    def __init__(self):
        self.client = None
        self.logged_in = False
        self.session_file = Path(settings.sessions_dir) / f"{settings.instagram_page_username}.json"

    async def initialize(self) -> bool:
        """
        Initialize and login to Instagram.

        Returns:
            True if login successful
        """
        if not settings.instagram_page_username or not settings.instagram_page_password:
            logger.error("Instagram credentials not configured")
            return False

        try:
            from instagrapi import Client

            self.client = Client()

            # Try to load existing session
            if self.session_file.exists():
                try:
                    self.client.load_settings(str(self.session_file))
                    self.client.login(
                        settings.instagram_page_username,
                        settings.instagram_page_password,
                    )
                    logger.info("Logged in using saved session")
                    self.logged_in = True
                    return True
                except Exception as e:
                    logger.warning(f"Session load failed, doing fresh login: {e}")

            # Fresh login
            self.client.login(
                settings.instagram_page_username,
                settings.instagram_page_password,
            )

            # Save session for future use
            self.session_file.parent.mkdir(parents=True, exist_ok=True)
            self.client.dump_settings(str(self.session_file))

            logger.info(f"Logged in as @{settings.instagram_page_username}")
            self.logged_in = True
            return True

        except ImportError:
            logger.error("instagrapi not installed")
            return False
        except Exception as e:
            logger.error(f"Instagram login failed: {e}")
            self.logged_in = False
            return False

    async def publish_image(
        self,
        image_path: str,
        caption: str,
    ) -> Optional[str]:
        """
        Publish a single image post.

        Args:
            image_path: Path to image file
            caption: Post caption

        Returns:
            Instagram media ID if successful, None otherwise
        """
        if not self.logged_in:
            if not await self.initialize():
                return None

        try:
            media = self.client.photo_upload(
                path=image_path,
                caption=caption,
            )
            logger.info(f"Published image post: {media.pk}")
            return str(media.pk)

        except Exception as e:
            logger.error(f"Failed to publish image: {e}")
            return None

    async def publish_carousel(
        self,
        image_paths: List[str],
        caption: str,
    ) -> Optional[str]:
        """
        Publish a carousel (album) post.

        Args:
            image_paths: List of paths to image files
            caption: Post caption

        Returns:
            Instagram media ID if successful, None otherwise
        """
        if not self.logged_in:
            if not await self.initialize():
                return None

        if not image_paths:
            logger.error("No images provided for carousel")
            return None

        try:
            media = self.client.album_upload(
                paths=image_paths,
                caption=caption,
            )
            logger.info(f"Published carousel post: {media.pk}")
            return str(media.pk)

        except Exception as e:
            logger.error(f"Failed to publish carousel: {e}")
            return None

    async def publish_reel(
        self,
        video_path: str,
        caption: str,
        thumbnail_path: str = None,
    ) -> Optional[str]:
        """
        Publish a reel (short video).

        Args:
            video_path: Path to video file
            caption: Post caption
            thumbnail_path: Optional thumbnail image

        Returns:
            Instagram media ID if successful, None otherwise
        """
        if not self.logged_in:
            if not await self.initialize():
                return None

        try:
            media = self.client.clip_upload(
                path=video_path,
                caption=caption,
                thumbnail=thumbnail_path,
            )
            logger.info(f"Published reel: {media.pk}")
            return str(media.pk)

        except Exception as e:
            logger.error(f"Failed to publish reel: {e}")
            return None

    async def get_media_insights(
        self,
        media_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get insights/engagement for a published post.

        Args:
            media_id: Instagram media ID

        Returns:
            Dict with engagement metrics
        """
        if not self.logged_in:
            if not await self.initialize():
                return None

        try:
            media_info = self.client.media_info(media_id)

            return {
                "like_count": media_info.like_count,
                "comment_count": media_info.comment_count,
                "play_count": getattr(media_info, "play_count", None),
                "view_count": getattr(media_info, "view_count", None),
            }

        except Exception as e:
            logger.error(f"Failed to get media insights: {e}")
            return None

    async def get_account_insights(self) -> Optional[Dict[str, Any]]:
        """
        Get account-level insights.

        Returns:
            Dict with account metrics
        """
        if not self.logged_in:
            if not await self.initialize():
                return None

        try:
            user_info = self.client.account_info()

            return {
                "username": user_info.username,
                "follower_count": user_info.follower_count,
                "following_count": user_info.following_count,
                "media_count": user_info.media_count,
            }

        except Exception as e:
            logger.error(f"Failed to get account insights: {e}")
            return None

    async def delete_media(self, media_id: str) -> bool:
        """
        Delete a published post.

        Args:
            media_id: Instagram media ID

        Returns:
            True if deleted successfully
        """
        if not self.logged_in:
            if not await self.initialize():
                return False

        try:
            self.client.media_delete(media_id)
            logger.info(f"Deleted media: {media_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete media: {e}")
            return False


class MockInstagramPublisher(InstagramPublisher):
    """
    Mock publisher for testing without actual Instagram API calls.
    """

    def __init__(self):
        super().__init__()
        self.published_posts: List[Dict] = []

    async def initialize(self) -> bool:
        """Mock initialization always succeeds."""
        self.logged_in = True
        return True

    async def publish_image(
        self,
        image_path: str,
        caption: str,
    ) -> Optional[str]:
        """Mock image publishing."""
        mock_id = f"mock_{datetime.utcnow().timestamp()}"
        self.published_posts.append({
            "id": mock_id,
            "type": "image",
            "path": image_path,
            "caption": caption,
            "timestamp": datetime.utcnow().isoformat(),
        })
        logger.info(f"[MOCK] Published image: {mock_id}")
        return mock_id

    async def publish_carousel(
        self,
        image_paths: List[str],
        caption: str,
    ) -> Optional[str]:
        """Mock carousel publishing."""
        mock_id = f"mock_{datetime.utcnow().timestamp()}"
        self.published_posts.append({
            "id": mock_id,
            "type": "carousel",
            "paths": image_paths,
            "caption": caption,
            "timestamp": datetime.utcnow().isoformat(),
        })
        logger.info(f"[MOCK] Published carousel: {mock_id}")
        return mock_id

    async def get_media_insights(
        self,
        media_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Mock insights."""
        import random
        return {
            "like_count": random.randint(100, 10000),
            "comment_count": random.randint(10, 500),
        }


def get_publisher(mock: bool = False) -> InstagramPublisher:
    """
    Get the appropriate publisher instance.

    Args:
        mock: Use mock publisher for testing

    Returns:
        InstagramPublisher instance
    """
    if mock or settings.environment == "development":
        return MockInstagramPublisher()
    return InstagramPublisher()
