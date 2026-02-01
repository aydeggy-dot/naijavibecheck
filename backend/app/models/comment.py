"""Comment model for extracted Instagram comments."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.post import Post
    from app.models.analysis import CommentAnalysis


class Comment(Base):
    """Comment extracted from an Instagram post."""

    __tablename__ = "comments"
    __table_args__ = (
        UniqueConstraint("post_id", "instagram_comment_id", name="uq_post_comment"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    instagram_comment_id: Mapped[Optional[str]] = mapped_column(String(255))
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    username_anonymized: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Username with asterisks for privacy",
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    commented_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
    is_reply: Mapped[bool] = mapped_column(Boolean, default=False)
    parent_comment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("comments.id", ondelete="SET NULL"),
    )

    # Relationships
    post: Mapped["Post"] = relationship(
        "Post",
        back_populates="comments",
    )
    analysis: Mapped[Optional["CommentAnalysis"]] = relationship(
        "CommentAnalysis",
        back_populates="comment",
        uselist=False,
        cascade="all, delete-orphan",
    )
    replies: Mapped[list["Comment"]] = relationship(
        "Comment",
        remote_side=[id],
        back_populates="parent",
    )
    parent: Mapped[Optional["Comment"]] = relationship(
        "Comment",
        remote_side=[parent_comment_id],
        back_populates="replies",
    )

    def __repr__(self) -> str:
        return f"<Comment by {self.username_anonymized}>"
