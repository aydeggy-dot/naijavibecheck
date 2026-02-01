"""Pydantic schemas for Comment model."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CommentBase(BaseModel):
    """Base schema for Comment."""

    username_anonymized: str
    text: str
    like_count: int = 0
    commented_at: Optional[datetime] = None
    is_reply: bool = False


class CommentResponse(CommentBase):
    """Schema for Comment response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    post_id: UUID
    scraped_at: datetime


class CommentAnalysisData(BaseModel):
    """Schema for Comment analysis data."""

    sentiment: str
    sentiment_score: float
    toxicity_score: float
    emotion_tags: Optional[list[str]] = None
    is_top_positive: bool = False
    is_top_negative: bool = False


class CommentWithAnalysis(CommentResponse):
    """Schema for Comment with analysis data."""

    analysis: Optional[CommentAnalysisData] = None
