"""Celery tasks for Instagram scraping."""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import selectinload

from app.workers.celery_app import celery_app
from app.database import SyncSessionLocal
from app.models import Celebrity, Post, Comment, ScraperAccount
from app.services.analyzer.viral_scorer import ViralScorer
from app.services.scraper import (
    InstagramScraper,
    InstagramScraperError,
    InstagramLoginError,
    InstagramRateLimitError,
    SyncAccountManager,
)
from app.config import settings

logger = logging.getLogger(__name__)


def run_async(coro):
    """Helper to run async code in sync Celery tasks."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3)
def scrape_all_celebrities(self):
    """
    Scrape all active celebrities for new posts.

    This task:
    1. Gets all active celebrities ordered by priority
    2. Checks each for new posts
    3. Identifies viral posts based on thresholds
    4. Stores new posts in the database
    """
    logger.info("Starting celebrity scraping task")

    try:
        db = SyncSessionLocal()

        # Get active celebrities ordered by priority
        celebrities = (
            db.query(Celebrity)
            .filter(Celebrity.is_active == True)
            .order_by(Celebrity.scrape_priority.desc())
            .all()
        )

        logger.info(f"Found {len(celebrities)} active celebrities to scrape")

        # Queue individual scrape tasks for each celebrity
        for celeb in celebrities:
            scrape_celebrity.delay(str(celeb.id))

        db.close()
        return {"status": "queued", "celebrities": len(celebrities)}

    except Exception as e:
        logger.error(f"Error in scrape_all_celebrities: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def scrape_celebrity(self, celebrity_id: str):
    """
    Scrape a specific celebrity for new posts.

    This task:
    1. Gets the celebrity from the database
    2. Uses the scraper service to fetch recent posts
    3. Stores new posts and marks them as viral if they meet thresholds
    """
    logger.info(f"Scraping celebrity: {celebrity_id}")

    db = SyncSessionLocal()

    try:
        celeb = db.query(Celebrity).filter(Celebrity.id == celebrity_id).first()

        if not celeb:
            logger.warning(f"Celebrity {celebrity_id} not found")
            db.close()
            return {"status": "not_found"}

        # Run the async scraping
        result = run_async(_scrape_celebrity_async(celeb, db))

        # Update last scraped timestamp
        celeb.last_scraped_at = datetime.utcnow()
        db.commit()

        logger.info(f"Finished scraping @{celeb.instagram_username}")
        db.close()
        return result

    except InstagramRateLimitError as e:
        logger.warning(f"Rate limit hit for {celebrity_id}: {e}")
        db.close()
        raise self.retry(exc=e, countdown=300)  # Wait 5 minutes

    except InstagramLoginError as e:
        logger.error(f"Login error scraping {celebrity_id}: {e}")
        db.close()
        return {"status": "login_error", "error": str(e)}

    except Exception as e:
        logger.error(f"Error scraping celebrity {celebrity_id}: {e}")
        db.close()
        raise self.retry(exc=e, countdown=120)


async def _scrape_celebrity_async(celeb: Celebrity, db) -> dict:
    """Async helper to scrape a celebrity's posts."""
    scraper = InstagramScraper()

    try:
        await scraper.initialize()

        # Fetch profile to update follower count
        profile = await scraper.get_profile(celeb.instagram_username)
        if profile:
            celeb.follower_count = profile.get("follower_count")
            celeb.is_verified = profile.get("is_verified", False)
            if not celeb.full_name and profile.get("full_name"):
                celeb.full_name = profile["full_name"]

        # Fetch recent posts
        posts = await scraper.get_recent_posts(
            celeb.instagram_username,
            max_posts=20,
            max_age_days=settings.max_post_age_days,
        )

        viral_scorer = ViralScorer()
        new_posts = 0
        viral_posts = 0

        for post_data in posts:
            # Check if post already exists
            existing = (
                db.query(Post)
                .filter(Post.instagram_post_id == post_data["post_id"])
                .first()
            )

            if existing:
                # Update engagement counts
                existing.like_count = post_data.get("like_count", existing.like_count)
                existing.comment_count = post_data.get("comment_count", existing.comment_count)
                continue

            # Check if viral
            is_viral = viral_scorer.is_viral(
                likes=post_data.get("like_count", 0),
                comments=post_data.get("comment_count", 0),
                posted_at=post_data.get("posted_at"),
            )

            viral_score = None
            if is_viral:
                viral_score = viral_scorer.calculate_viral_score(
                    likes=post_data.get("like_count", 0),
                    comments=post_data.get("comment_count", 0),
                    posted_at=post_data.get("posted_at"),
                    follower_count=celeb.follower_count,
                )
                viral_posts += 1

            # Create new post
            new_post = Post(
                celebrity_id=celeb.id,
                instagram_post_id=post_data["post_id"],
                shortcode=post_data["shortcode"],
                post_url=post_data.get("post_url"),
                caption=post_data.get("caption"),
                like_count=post_data.get("like_count"),
                comment_count=post_data.get("comment_count"),
                posted_at=post_data.get("posted_at"),
                scraped_at=datetime.utcnow(),
                is_viral=is_viral,
                viral_score=viral_score,
                metadata_={
                    "media_type": post_data.get("media_type"),
                    "thumbnail_url": post_data.get("thumbnail_url"),
                },
            )
            db.add(new_post)
            new_posts += 1

            # Queue comment extraction for viral posts
            if is_viral:
                db.flush()  # Get the post ID
                extract_post_comments.delay(str(new_post.id))

        db.commit()

        return {
            "status": "success",
            "username": celeb.instagram_username,
            "new_posts": new_posts,
            "viral_posts": viral_posts,
        }

    finally:
        await scraper.close()


@celery_app.task(bind=True)
def detect_viral_posts(self):
    """
    Scan recent posts and mark viral ones for processing.

    This task:
    1. Gets all recent posts that aren't marked viral
    2. Evaluates them against viral thresholds
    3. Marks qualifying posts as viral
    4. Queues them for analysis
    """
    logger.info("Detecting viral posts")

    try:
        db = SyncSessionLocal()
        viral_scorer = ViralScorer()

        # Get recent unprocessed posts
        posts = (
            db.query(Post)
            .options(selectinload(Post.celebrity))
            .filter(Post.is_viral == False)
            .filter(Post.is_analyzed == False)
            .order_by(Post.scraped_at.desc())
            .limit(200)
            .all()
        )

        logger.info(f"Checking {len(posts)} posts for viral status")

        viral_found = 0
        for post in posts:
            follower_count = post.celebrity.follower_count if post.celebrity else None

            # Check if meets viral thresholds
            is_viral = viral_scorer.is_viral(
                likes=post.like_count or 0,
                comments=post.comment_count or 0,
                posted_at=post.posted_at,
            )

            if is_viral:
                # Calculate viral score
                score = viral_scorer.calculate_viral_score(
                    likes=post.like_count or 0,
                    comments=post.comment_count or 0,
                    posted_at=post.posted_at,
                    follower_count=follower_count,
                )

                post.is_viral = True
                post.viral_score = score
                viral_found += 1

                logger.info(
                    f"Viral post found: {post.shortcode} by "
                    f"@{post.celebrity.instagram_username if post.celebrity else 'unknown'} "
                    f"(score: {score:.1f})"
                )

                # Queue for comment extraction and analysis
                extract_post_comments.delay(str(post.id))

        db.commit()
        db.close()

        logger.info(f"Found {viral_found} new viral posts")
        return {"status": "complete", "viral_posts_found": viral_found}

    except Exception as e:
        logger.error(f"Error detecting viral posts: {e}")
        raise


@celery_app.task(bind=True, max_retries=3)
def extract_post_comments(self, post_id: str):
    """
    Extract comments from a viral post.

    This task:
    1. Gets the post from database
    2. Uses scraper to extract comments
    3. Stores comments with anonymized usernames
    4. Queues post for sentiment analysis
    """
    logger.info(f"Extracting comments for post: {post_id}")

    db = SyncSessionLocal()

    try:
        post = (
            db.query(Post)
            .options(selectinload(Post.celebrity))
            .filter(Post.id == post_id)
            .first()
        )

        if not post:
            logger.warning(f"Post {post_id} not found")
            db.close()
            return {"status": "not_found"}

        # Run async comment extraction
        result = run_async(_extract_comments_async(post, db))

        db.close()

        # Queue for analysis if comments were extracted
        if result.get("comments_extracted", 0) > 0:
            from app.workers.analysis_tasks import analyze_post_sync
            analyze_post_sync.delay(post_id)

        return result

    except InstagramRateLimitError as e:
        logger.warning(f"Rate limit hit extracting comments for {post_id}: {e}")
        db.close()
        raise self.retry(exc=e, countdown=300)

    except Exception as e:
        logger.error(f"Error extracting comments for {post_id}: {e}")
        db.close()
        raise self.retry(exc=e, countdown=120)


async def _extract_comments_async(post: Post, db) -> dict:
    """Async helper to extract comments from a post."""
    scraper = InstagramScraper()

    try:
        await scraper.initialize()

        # Fetch comments
        comments_data = await scraper.get_post_comments(
            post.shortcode,
            max_comments=500,
        )

        if not comments_data:
            logger.info(f"No comments found for post {post.shortcode}")
            return {"status": "no_comments", "post_id": str(post.id)}

        new_comments = 0

        for comment_data in comments_data:
            # Check if comment already exists
            existing = (
                db.query(Comment)
                .filter(Comment.post_id == post.id)
                .filter(Comment.instagram_comment_id == comment_data["comment_id"])
                .first()
            )

            if existing:
                continue

            # Create new comment
            new_comment = Comment(
                post_id=post.id,
                instagram_comment_id=comment_data["comment_id"],
                username=comment_data["username"],
                username_anonymized=comment_data["username_anonymized"],
                text=comment_data["text"],
                like_count=comment_data.get("like_count", 0),
                commented_at=comment_data.get("commented_at"),
                scraped_at=datetime.utcnow(),
                is_reply=comment_data.get("is_reply", False),
            )
            db.add(new_comment)
            new_comments += 1

        db.commit()

        logger.info(
            f"Extracted {new_comments} new comments for post {post.shortcode}"
        )

        return {
            "status": "success",
            "post_id": str(post.id),
            "comments_extracted": new_comments,
            "total_comments": len(comments_data),
        }

    finally:
        await scraper.close()


@celery_app.task
def reset_daily_counters():
    """Reset daily request counters for scraper accounts."""
    logger.info("Resetting daily request counters")

    try:
        db = SyncSessionLocal()

        accounts = db.query(ScraperAccount).all()
        for account in accounts:
            account.requests_today = 0

        db.commit()
        db.close()

        logger.info(f"Reset counters for {len(accounts)} accounts")
        return {"status": "success", "accounts_reset": len(accounts)}

    except Exception as e:
        logger.error(f"Error resetting counters: {e}")
        raise


@celery_app.task(bind=True)
def scrape_trending_hashtags(self):
    """
    Scrape trending Nigerian hashtags for celebrity discovery.
    """
    logger.info("Scraping trending hashtags")

    hashtags = [
        "naijacelebs",
        "nollywood",
        "afrobeats",
        "naijamusicislifestyle",
        "lagoscelebs",
        "naijagist",
        "naijatiktok",
    ]

    # TODO: Implement hashtag scraping for celebrity discovery
    # This would use scraper.get_hashtag_medias() to find popular posts

    return {"status": "complete", "hashtags_checked": len(hashtags)}


@celery_app.task(bind=True)
def update_celebrity_followers(self):
    """
    Update follower counts for tracked celebrities.
    """
    logger.info("Updating celebrity follower counts")

    db = SyncSessionLocal()

    try:
        celebrities = (
            db.query(Celebrity)
            .filter(Celebrity.is_active == True)
            .all()
        )

        result = run_async(_update_followers_async(celebrities, db))

        db.commit()
        db.close()

        return result

    except Exception as e:
        logger.error(f"Error updating follower counts: {e}")
        db.close()
        raise


async def _update_followers_async(celebrities: list, db) -> dict:
    """Async helper to update follower counts."""
    scraper = InstagramScraper()
    updated = 0

    try:
        await scraper.initialize()

        for celeb in celebrities:
            try:
                profile = await scraper.get_profile(celeb.instagram_username)
                if profile:
                    celeb.follower_count = profile.get("follower_count")
                    celeb.is_verified = profile.get("is_verified", False)
                    updated += 1

            except InstagramRateLimitError:
                logger.warning(f"Rate limited while updating @{celeb.instagram_username}")
                break

            except Exception as e:
                logger.warning(f"Failed to update @{celeb.instagram_username}: {e}")

        return {"status": "complete", "updated": updated}

    finally:
        await scraper.close()


@celery_app.task(bind=True, max_retries=2)
def scrape_single_post(self, shortcode: str, celebrity_id: Optional[str] = None):
    """
    Scrape a single post by shortcode.

    Useful for manually adding specific viral posts.
    """
    logger.info(f"Scraping single post: {shortcode}")

    db = SyncSessionLocal()

    try:
        result = run_async(_scrape_single_post_async(shortcode, celebrity_id, db))
        db.close()
        return result

    except Exception as e:
        logger.error(f"Error scraping post {shortcode}: {e}")
        db.close()
        raise self.retry(exc=e, countdown=60)


async def _scrape_single_post_async(shortcode: str, celebrity_id: Optional[str], db) -> dict:
    """Async helper to scrape a single post."""
    scraper = InstagramScraper()

    try:
        await scraper.initialize()

        post_data = await scraper.get_post_by_shortcode(shortcode)
        if not post_data:
            return {"status": "not_found", "shortcode": shortcode}

        # Check if post already exists
        existing = (
            db.query(Post)
            .filter(Post.shortcode == shortcode)
            .first()
        )

        if existing:
            # Update engagement counts
            existing.like_count = post_data.get("like_count", existing.like_count)
            existing.comment_count = post_data.get("comment_count", existing.comment_count)
            db.commit()
            return {"status": "updated", "post_id": str(existing.id)}

        # Find or create celebrity
        celeb_id = celebrity_id
        if not celeb_id and post_data.get("user"):
            username = post_data["user"]["username"]
            celeb = (
                db.query(Celebrity)
                .filter(Celebrity.instagram_username == username)
                .first()
            )
            if celeb:
                celeb_id = str(celeb.id)

        if not celeb_id:
            return {"status": "no_celebrity", "shortcode": shortcode}

        # Calculate viral score
        viral_scorer = ViralScorer()
        viral_score = viral_scorer.calculate_viral_score(
            likes=post_data.get("like_count", 0),
            comments=post_data.get("comment_count", 0),
            posted_at=post_data.get("posted_at"),
        )

        # Create new post
        new_post = Post(
            celebrity_id=celeb_id,
            instagram_post_id=post_data["post_id"],
            shortcode=post_data["shortcode"],
            post_url=post_data.get("post_url"),
            caption=post_data.get("caption"),
            like_count=post_data.get("like_count"),
            comment_count=post_data.get("comment_count"),
            posted_at=post_data.get("posted_at"),
            scraped_at=datetime.utcnow(),
            is_viral=True,  # Manually added posts are considered viral
            viral_score=viral_score,
        )
        db.add(new_post)
        db.commit()

        # Queue comment extraction
        extract_post_comments.delay(str(new_post.id))

        return {
            "status": "created",
            "post_id": str(new_post.id),
            "shortcode": shortcode,
        }

    finally:
        await scraper.close()
