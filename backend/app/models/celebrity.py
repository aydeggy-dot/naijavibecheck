"""Celebrity model for tracked Instagram accounts."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.post import Post


class Celebrity(Base):
    """Celebrity being tracked on Instagram."""

    __tablename__ = "celebrities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    instagram_username: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    category: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="musician, actor, influencer, athlete",
    )
    follower_count: Mapped[Optional[int]] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
    last_scraped_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    scrape_priority: Mapped[int] = mapped_column(
        Integer,
        default=5,
        comment="1-10, higher = more frequent",
    )
    metadata_: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
    )

    # Relationships
    posts: Mapped[list["Post"]] = relationship(
        "Post",
        back_populates="celebrity",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Celebrity @{self.instagram_username}>"


class CelebritySuggestion(Base):
    """User-submitted celebrity suggestions pending approval."""

    __tablename__ = "celebrity_suggestions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    instagram_username: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    category: Mapped[Optional[str]] = mapped_column(
        String(50),
        default="unknown",
        comment="musician, actor, comedian, influencer, unknown",
    )
    reason: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="Why this celebrity should be tracked",
    )
    submitted_by: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="User ID or email of submitter",
    )
    example_post_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="Example post URL that prompted suggestion",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        index=True,
        comment="pending, approved, rejected, duplicate",
    )
    vote_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Number of upvotes from other users",
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
    reviewed_by: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="Admin who reviewed this suggestion",
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<CelebritySuggestion @{self.instagram_username} ({self.status})>"
