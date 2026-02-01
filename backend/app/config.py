"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra env vars from .env file
    )

    # App
    app_name: str = "NaijaVibeCheck"
    debug: bool = False
    environment: str = "development"
    secret_key: str = "dev-secret-key-change-in-production"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Database
    database_url: str = "postgresql://naijavibecheck:naijavibecheck@localhost:5432/naijavibecheck"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Anthropic AI
    anthropic_api_key: Optional[str] = None

    # Instagram Scraper Account (throwaway account for scraping)
    instagram_scraper_username: Optional[str] = None
    instagram_scraper_password: Optional[str] = None

    # Instagram Main Page Account (for publishing content)
    instagram_page_username: Optional[str] = None
    instagram_page_password: Optional[str] = None

    # Storage (DigitalOcean Spaces)
    do_spaces_key: Optional[str] = None
    do_spaces_secret: Optional[str] = None
    do_spaces_bucket: str = "naijavibecheck-media"
    do_spaces_region: str = "nyc3"
    do_spaces_endpoint: Optional[str] = None

    # Scraping Settings
    max_scraper_accounts: int = 10
    requests_per_account_per_day: int = 100
    scrape_interval_minutes: int = 30

    # Viral Thresholds
    min_celebrity_followers: int = 1_500_000
    min_post_likes: int = 100_000
    min_post_comments: int = 25_000
    max_post_age_days: int = 3

    # Paths
    templates_dir: str = "templates"
    sessions_dir: str = "sessions"
    generated_media_dir: str = "generated_media"

    @property
    def async_database_url(self) -> str:
        """Get async database URL for asyncpg."""
        return self.database_url.replace("postgresql://", "postgresql+asyncpg://")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
