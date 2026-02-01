"""Pydantic schemas for Post model."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PostBase(BaseModel):
    """Base schema for Post."""

    instagram_post_id: str
    shortcode: str
    post_url: Optional[str] = None
    caption: Optional[str] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None
    posted_at: Optional[datetime] = None


class PostCreate(PostBase):
    """Schema for creating a Post."""

    celebrity_id: UUID


class PostResponse(PostBase):
    """Schema for Post response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    celebrity_id: UUID
    scraped_at: datetime
    is_viral: bool
    viral_score: Optional[float] = None
    is_analyzed: bool
    is_processed: bool
    celebrity_username: Optional[str] = Field(
        default=None,
        description="Celebrity's Instagram username",
    )


class PostListResponse(BaseModel):
    """Schema for paginated Post list."""

    items: list[PostResponse]
    total: int
    page: int
    page_size: int
    pages: int
