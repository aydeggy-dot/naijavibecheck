"""Pydantic schemas for Celebrity model."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CelebrityBase(BaseModel):
    """Base schema for Celebrity."""

    instagram_username: str = Field(..., max_length=255)
    full_name: Optional[str] = Field(None, max_length=255)
    category: Optional[str] = Field(
        None,
        max_length=50,
        description="musician, actor, influencer, athlete",
    )
    follower_count: Optional[int] = None
    is_active: bool = True
    scrape_priority: int = Field(
        default=5,
        ge=1,
        le=10,
        description="1-10, higher = more frequent scraping",
    )


class CelebrityCreate(CelebrityBase):
    """Schema for creating a Celebrity."""

    pass


class CelebrityUpdate(BaseModel):
    """Schema for updating a Celebrity."""

    instagram_username: Optional[str] = Field(None, max_length=255)
    full_name: Optional[str] = Field(None, max_length=255)
    category: Optional[str] = Field(None, max_length=50)
    follower_count: Optional[int] = None
    is_active: Optional[bool] = None
    scrape_priority: Optional[int] = Field(None, ge=1, le=10)


class CelebrityResponse(CelebrityBase):
    """Schema for Celebrity response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    discovered_at: datetime
    last_scraped_at: Optional[datetime] = None
    post_count: Optional[int] = Field(
        default=None,
        description="Number of posts scraped",
    )


class CelebrityListResponse(BaseModel):
    """Schema for paginated Celebrity list."""

    items: list[CelebrityResponse]
    total: int
    page: int
    page_size: int
    pages: int
