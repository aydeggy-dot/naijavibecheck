"""Settings and account management models."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Settings(Base):
    """System settings key-value store."""

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
    )
    value: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def __repr__(self) -> str:
        return f"<Settings {self.key}>"


class ScraperAccount(Base):
    """Throwaway Instagram accounts for scraping."""

    __tablename__ = "scraper_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    username: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    password_encrypted: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    session_data: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    requests_today: Mapped[int] = mapped_column(Integer, default=0)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    banned_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    proxy_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("proxies.id", ondelete="SET NULL"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    def __repr__(self) -> str:
        return f"<ScraperAccount @{self.username} active={self.is_active}>"


class Proxy(Base):
    """Proxy configuration for scraping."""

    __tablename__ = "proxies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(255))
    password_encrypted: Mapped[Optional[str]] = mapped_column(Text)
    protocol: Mapped[str] = mapped_column(
        String(20),
        default="http",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    country_code: Mapped[Optional[str]] = mapped_column(String(5))
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    def to_url(self) -> str:
        """Convert proxy config to URL format."""
        auth = ""
        if self.username and self.password_encrypted:
            # Note: In production, decrypt the password here
            auth = f"{self.username}:{self.password_encrypted}@"
        return f"{self.protocol}://{auth}{self.host}:{self.port}"

    def __repr__(self) -> str:
        return f"<Proxy {self.host}:{self.port}>"
