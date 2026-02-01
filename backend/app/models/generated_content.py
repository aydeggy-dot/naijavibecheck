"""Generated content model for Instagram posts we create."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.analysis import PostAnalysis
    from app.models.engagement import OurEngagement, ContentPerformance


class GeneratedContent(Base):
    """Content generated for our Instagram page."""

    __tablename__ = "generated_content"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    post_analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("post_analysis.id", ondelete="CASCADE"),
        nullable=False,
    )
    content_type: Mapped[str] = mapped_column(
        String(50),
        comment="image, carousel, reel",
    )
    title: Mapped[Optional[str]] = mapped_column(String(255))
    caption: Mapped[Optional[str]] = mapped_column(Text)
    hashtags: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String(50)))
    media_urls: Mapped[Optional[list[str]]] = mapped_column(
        ARRAY(Text),
        comment="URLs to generated images/videos",
    )
    thumbnail_url: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(50),
        default="draft",
        comment="draft, pending_review, approved, published, rejected",
    )
    scheduled_for: Mapped[Optional[datetime]] = mapped_column(DateTime)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    instagram_post_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="Instagram media ID after publishing",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    generation_metadata: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
    )

    # Relationships
    post_analysis: Mapped["PostAnalysis"] = relationship(
        "PostAnalysis",
        back_populates="generated_content",
    )
    engagement: Mapped[list["OurEngagement"]] = relationship(
        "OurEngagement",
        back_populates="content",
        cascade="all, delete-orphan",
    )
    performance: Mapped[Optional["ContentPerformance"]] = relationship(
        "ContentPerformance",
        back_populates="content",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<GeneratedContent {self.content_type} ({self.status})>"
