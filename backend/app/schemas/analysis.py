"""Pydantic schemas for Analysis models."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CommentAnalysisResponse(BaseModel):
    """Schema for CommentAnalysis response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    comment_id: UUID
    sentiment: str
    sentiment_score: float
    toxicity_score: float
    emotion_tags: Optional[list[str]] = None
    is_top_positive: bool
    is_top_negative: bool
    analyzed_at: datetime


class AnalysisStats(BaseModel):
    """Schema for analysis statistics."""

    total: int
    positive_count: int
    negative_count: int
    neutral_count: int
    positive_pct: float
    negative_pct: float
    neutral_pct: float
    average_sentiment: float
    controversy_score: Optional[float] = None


class AIInsights(BaseModel):
    """Schema for AI-generated insights."""

    headline: str
    vibe_summary: str
    spicy_take: Optional[str] = None
    controversy_level: str
    recommended_hashtags: list[str]


class PostAnalysisResponse(BaseModel):
    """Schema for PostAnalysis response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    post_id: UUID
    stats: AnalysisStats
    ai_summary: Optional[str] = None
    ai_insights: Optional[AIInsights] = None
    analyzed_at: datetime
    top_positive_comments: Optional[list[UUID]] = None
    top_negative_comments: Optional[list[UUID]] = None
