"""Celery application configuration."""

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "naijavibecheck",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.workers.scraping_tasks",
        "app.workers.analysis_tasks",
        "app.workers.generation_tasks",
        "app.workers.publishing_tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Africa/Lagos",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max per task
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Scheduled tasks (Celery Beat)
celery_app.conf.beat_schedule = {
    # Scrape celebrities every 30 minutes
    "scrape-celebrities-periodic": {
        "task": "app.workers.scraping_tasks.scrape_all_celebrities",
        "schedule": crontab(minute=f"*/{settings.scrape_interval_minutes}"),
    },
    # Check for viral posts every hour
    "detect-viral-posts": {
        "task": "app.workers.scraping_tasks.detect_viral_posts",
        "schedule": crontab(minute=0),  # Every hour
    },
    # Process pending analyses every 15 minutes
    "process-pending-analyses": {
        "task": "app.workers.analysis_tasks.process_pending_analyses",
        "schedule": crontab(minute="*/15"),
    },
    # Update viral scores every 2 hours
    "update-viral-scores": {
        "task": "app.workers.analysis_tasks.update_viral_scores",
        "schedule": crontab(minute=30, hour="*/2"),
    },
    # Publish scheduled content (check every 5 minutes)
    "publish-scheduled-content": {
        "task": "app.workers.publishing_tasks.publish_scheduled_content",
        "schedule": crontab(minute="*/5"),
    },
    # Track engagement for published posts daily
    "track-engagement": {
        "task": "app.workers.publishing_tasks.track_engagement",
        "schedule": crontab(hour=6, minute=0),  # 6 AM Lagos time
    },
    # Reset daily request counters at midnight
    "reset-daily-counters": {
        "task": "app.workers.scraping_tasks.reset_daily_counters",
        "schedule": crontab(hour=0, minute=0),
    },
    # Update celebrity follower counts daily
    "update-celebrity-followers": {
        "task": "app.workers.scraping_tasks.update_celebrity_followers",
        "schedule": crontab(hour=3, minute=0),  # 3 AM Lagos time
    },
    # Process content generation queue every 20 minutes
    "process-content-queue": {
        "task": "app.workers.generation_tasks.process_content_queue",
        "schedule": crontab(minute="*/20"),
    },
    # Clean up old media weekly
    "cleanup-old-media": {
        "task": "app.workers.generation_tasks.cleanup_old_media",
        "schedule": crontab(hour=4, minute=0, day_of_week=0),  # Sunday 4 AM
    },
    # Update account stats every 6 hours
    "update-account-stats": {
        "task": "app.workers.publishing_tasks.update_account_stats",
        "schedule": crontab(minute=0, hour="*/6"),
    },
}
