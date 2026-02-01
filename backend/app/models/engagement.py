"""Engagement tracking models for our Instagram page."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.generated_content import GeneratedContent


class OurEngagement(Base):
    """Engagement metrics for our published posts."""

    __tablename__ = "our_engagement"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    generated_content_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("generated_content.id", ondelete="CASCADE"),
        nullable=False,
    )
    checked_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
    like_count: Mapped[Optional[int]] = mapped_column(Integer)
    comment_count: Mapped[Optional[int]] = mapped_column(Integer)
    share_count: Mapped[Optional[int]] = mapped_column(Integer)
    save_count: Mapped[Optional[int]] = mapped_column(Integer)
    reach: Mapped[Optional[int]] = mapped_column(Integer)
    impressions: Mapped[Optional[int]] = mapped_column(Integer)
    engagement_rate: Mapped[Optional[float]] = mapped_column(Float)
    follower_change: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="Net follower change after this post",
    )

    # Relationships
    content: Mapped["GeneratedContent"] = relationship(
        "GeneratedContent",
        back_populates="engagement",
    )

    def __repr__(self) -> str:
        return f"<OurEngagement likes={self.like_count} engagement={self.engagement_rate:.2%}>"


class ContentPerformance(Base):
    """Learning data for content optimization."""

    __tablename__ = "content_performance"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    generated_content_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("generated_content.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    celebrity_category: Mapped[Optional[str]] = mapped_column(String(50))
    content_type: Mapped[Optional[str]] = mapped_column(String(50))
    post_hour: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="0-23",
    )
    post_day_of_week: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="0-6 (Monday=0)",
    )
    controversy_level: Mapped[Optional[str]] = mapped_column(
        String(20),
        comment="low, medium, high",
    )
    engagement_score: Mapped[Optional[float]] = mapped_column(Float)
    virality_score: Mapped[Optional[float]] = mapped_column(Float)
    features: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        comment="ML features for learning",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    # Relationships
    content: Mapped["GeneratedContent"] = relationship(
        "GeneratedContent",
        back_populates="performance",
    )

    def __repr__(self) -> str:
        return f"<ContentPerformance score={self.engagement_score}>"
