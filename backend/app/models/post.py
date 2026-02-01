"""Post model for viral Instagram posts."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.celebrity import Celebrity
    from app.models.comment import Comment
    from app.models.analysis import PostAnalysis


class Post(Base):
    """Viral post detected from a celebrity."""

    __tablename__ = "posts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    celebrity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("celebrities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    instagram_post_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )
    shortcode: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    post_url: Mapped[Optional[str]] = mapped_column(String(500))
    caption: Mapped[Optional[str]] = mapped_column(Text)
    like_count: Mapped[Optional[int]] = mapped_column(Integer)
    comment_count: Mapped[Optional[int]] = mapped_column(Integer)
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
    is_viral: Mapped[bool] = mapped_column(Boolean, default=False)
    viral_score: Mapped[Optional[float]] = mapped_column(Float)
    is_analyzed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_processed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Content has been generated",
    )
    metadata_: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
    )

    # Relationships
    celebrity: Mapped["Celebrity"] = relationship(
        "Celebrity",
        back_populates="posts",
    )
    comments: Mapped[list["Comment"]] = relationship(
        "Comment",
        back_populates="post",
        cascade="all, delete-orphan",
    )
    analysis: Mapped[Optional["PostAnalysis"]] = relationship(
        "PostAnalysis",
        back_populates="post",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Post {self.shortcode}>"
