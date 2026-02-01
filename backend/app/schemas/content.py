"""Pydantic schemas for GeneratedContent model."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ContentStatus(str, Enum):
    """Content status enum."""

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    REJECTED = "rejected"


class ContentType(str, Enum):
    """Content type enum."""

    IMAGE = "image"
    CAROUSEL = "carousel"
    REEL = "reel"


class GeneratedContentBase(BaseModel):
    """Base schema for GeneratedContent."""

    content_type: ContentType
    title: Optional[str] = Field(None, max_length=255)
    caption: Optional[str] = None
    hashtags: Optional[list[str]] = None


class GeneratedContentCreate(GeneratedContentBase):
    """Schema for creating GeneratedContent."""

    post_analysis_id: UUID
    media_urls: Optional[list[str]] = None
    thumbnail_url: Optional[str] = None


class GeneratedContentUpdate(BaseModel):
    """Schema for updating GeneratedContent."""

    title: Optional[str] = Field(None, max_length=255)
    caption: Optional[str] = None
    hashtags: Optional[list[str]] = None
    status: Optional[ContentStatus] = None
    scheduled_for: Optional[datetime] = None


class GeneratedContentResponse(GeneratedContentBase):
    """Schema for GeneratedContent response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    post_analysis_id: UUID
    status: ContentStatus
    media_urls: Optional[list[str]] = None
    thumbnail_url: Optional[str] = None
    scheduled_for: Optional[datetime] = None
    published_at: Optional[datetime] = None
    instagram_post_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ContentQueueResponse(BaseModel):
    """Schema for content queue response."""

    pending: list[GeneratedContentResponse]
    approved: list[GeneratedContentResponse]
    published: list[GeneratedContentResponse]
    rejected: list[GeneratedContentResponse]
    total: int
