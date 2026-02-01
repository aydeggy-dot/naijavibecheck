"""Analysis models for sentiment analysis results."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.comment import Comment
    from app.models.post import Post
    from app.models.generated_content import GeneratedContent


class CommentAnalysis(Base):
    """Sentiment analysis result for a single comment."""

    __tablename__ = "comment_analysis"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    comment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("comments.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    sentiment: Mapped[str] = mapped_column(
        String(20),
        comment="positive, negative, neutral",
    )
    sentiment_score: Mapped[float] = mapped_column(
        Float,
        comment="-1.0 to 1.0",
    )
    toxicity_score: Mapped[float] = mapped_column(
        Float,
        comment="0.0 to 1.0",
    )
    emotion_tags: Mapped[Optional[list[str]]] = mapped_column(
        ARRAY(String(50)),
        comment="funny, angry, supportive, etc.",
    )
    is_top_positive: Mapped[bool] = mapped_column(default=False)
    is_top_negative: Mapped[bool] = mapped_column(default=False)
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
    analysis_metadata: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
    )

    # Relationships
    comment: Mapped["Comment"] = relationship(
        "Comment",
        back_populates="analysis",
    )

    def __repr__(self) -> str:
        return f"<CommentAnalysis {self.sentiment} ({self.sentiment_score:.2f})>"


class PostAnalysis(Base):
    """Post-level analysis summary."""

    __tablename__ = "post_analysis"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("posts.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    total_comments_analyzed: Mapped[int] = mapped_column(Integer)
    positive_count: Mapped[int] = mapped_column(Integer, default=0)
    negative_count: Mapped[int] = mapped_column(Integer, default=0)
    neutral_count: Mapped[int] = mapped_column(Integer, default=0)
    positive_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    negative_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    neutral_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    average_sentiment_score: Mapped[float] = mapped_column(Float, default=0.0)
    top_positive_comment_ids: Mapped[Optional[list[uuid.UUID]]] = mapped_column(
        ARRAY(UUID(as_uuid=True)),
    )
    top_negative_comment_ids: Mapped[Optional[list[uuid.UUID]]] = mapped_column(
        ARRAY(UUID(as_uuid=True)),
    )
    controversy_score: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="How divisive the post is",
    )
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
    # AI-generated content
    headline: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="Catchy Nigerian-style headline",
    )
    vibe_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="2-3 sentence summary in Nigerian style",
    )
    spicy_take: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="Witty observation about the comments",
    )
    controversy_level: Mapped[Optional[str]] = mapped_column(
        String(20),
        comment="chill, mid, or wahala",
    )
    themes: Mapped[Optional[list[str]]] = mapped_column(
        ARRAY(String(100)),
        comment="Key themes in comments",
    )
    recommended_hashtags: Mapped[Optional[list[str]]] = mapped_column(
        ARRAY(String(50)),
        comment="Suggested hashtags",
    )
    # Store top comments as JSON for easy retrieval
    top_positive_comments: Mapped[dict] = mapped_column(
        JSONB,
        default=list,
        comment="Top positive comments with text",
    )
    top_negative_comments: Mapped[dict] = mapped_column(
        JSONB,
        default=list,
        comment="Top negative comments with text",
    )
    notable_comments: Mapped[dict] = mapped_column(
        JSONB,
        default=list,
        comment="Notable/viral-worthy comments",
    )
    # Legacy fields
    ai_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="Claude's summary of the vibe (legacy)",
    )
    ai_insights: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        comment="Additional AI insights",
    )
    # Metadata
    analysis_cost: Mapped[Optional[float]] = mapped_column(
        Float,
        comment="Estimated cost in USD",
    )
    analysis_method: Mapped[Optional[str]] = mapped_column(
        String(50),
        default="cost_effective",
        comment="cost_effective or full_claude",
    )

    # Relationships
    post: Mapped["Post"] = relationship(
        "Post",
        back_populates="analysis",
    )
    generated_content: Mapped[list["GeneratedContent"]] = relationship(
        "GeneratedContent",
        back_populates="post_analysis",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<PostAnalysis pos={self.positive_percentage:.1f}% neg={self.negative_percentage:.1f}%>"
