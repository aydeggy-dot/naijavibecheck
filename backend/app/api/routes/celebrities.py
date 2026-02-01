"""Celebrity API endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models import Celebrity, Post
from app.schemas.celebrity import (
    CelebrityCreate,
    CelebrityListResponse,
    CelebrityResponse,
    CelebrityUpdate,
)

router = APIRouter()


@router.get("", response_model=CelebrityListResponse)
async def list_celebrities(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all celebrities with pagination and filtering."""
    query = select(Celebrity)

    # Apply filters
    if is_active is not None:
        query = query.where(Celebrity.is_active == is_active)
    if category:
        query = query.where(Celebrity.category == category)
    if search:
        query = query.where(
            Celebrity.instagram_username.ilike(f"%{search}%")
            | Celebrity.full_name.ilike(f"%{search}%")
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Apply pagination
    query = query.order_by(Celebrity.scrape_priority.desc(), Celebrity.discovered_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    celebrities = result.scalars().all()

    # Get post counts
    items = []
    for celeb in celebrities:
        post_count_query = select(func.count()).where(Post.celebrity_id == celeb.id)
        post_count = await db.scalar(post_count_query)
        celeb_dict = {
            "id": celeb.id,
            "instagram_username": celeb.instagram_username,
            "full_name": celeb.full_name,
            "category": celeb.category,
            "follower_count": celeb.follower_count,
            "is_active": celeb.is_active,
            "scrape_priority": celeb.scrape_priority,
            "discovered_at": celeb.discovered_at,
            "last_scraped_at": celeb.last_scraped_at,
            "post_count": post_count,
        }
        items.append(CelebrityResponse(**celeb_dict))

    return CelebrityListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=CelebrityResponse, status_code=201)
async def create_celebrity(
    data: CelebrityCreate,
    db: AsyncSession = Depends(get_db),
):
    """Add a new celebrity to track."""
    # Check if already exists
    existing = await db.execute(
        select(Celebrity).where(Celebrity.instagram_username == data.instagram_username)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Celebrity @{data.instagram_username} already exists",
        )

    celebrity = Celebrity(**data.model_dump())
    db.add(celebrity)
    await db.commit()
    await db.refresh(celebrity)

    return CelebrityResponse(
        id=celebrity.id,
        instagram_username=celebrity.instagram_username,
        full_name=celebrity.full_name,
        category=celebrity.category,
        follower_count=celebrity.follower_count,
        is_active=celebrity.is_active,
        scrape_priority=celebrity.scrape_priority,
        discovered_at=celebrity.discovered_at,
        last_scraped_at=celebrity.last_scraped_at,
        post_count=0,
    )


@router.get("/{celebrity_id}", response_model=CelebrityResponse)
async def get_celebrity(
    celebrity_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific celebrity by ID."""
    result = await db.execute(select(Celebrity).where(Celebrity.id == celebrity_id))
    celebrity = result.scalar_one_or_none()

    if not celebrity:
        raise HTTPException(status_code=404, detail="Celebrity not found")

    post_count_query = select(func.count()).where(Post.celebrity_id == celebrity.id)
    post_count = await db.scalar(post_count_query)

    return CelebrityResponse(
        id=celebrity.id,
        instagram_username=celebrity.instagram_username,
        full_name=celebrity.full_name,
        category=celebrity.category,
        follower_count=celebrity.follower_count,
        is_active=celebrity.is_active,
        scrape_priority=celebrity.scrape_priority,
        discovered_at=celebrity.discovered_at,
        last_scraped_at=celebrity.last_scraped_at,
        post_count=post_count,
    )


@router.patch("/{celebrity_id}", response_model=CelebrityResponse)
async def update_celebrity(
    celebrity_id: UUID,
    data: CelebrityUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a celebrity's information."""
    result = await db.execute(select(Celebrity).where(Celebrity.id == celebrity_id))
    celebrity = result.scalar_one_or_none()

    if not celebrity:
        raise HTTPException(status_code=404, detail="Celebrity not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(celebrity, field, value)

    await db.commit()
    await db.refresh(celebrity)

    post_count_query = select(func.count()).where(Post.celebrity_id == celebrity.id)
    post_count = await db.scalar(post_count_query)

    return CelebrityResponse(
        id=celebrity.id,
        instagram_username=celebrity.instagram_username,
        full_name=celebrity.full_name,
        category=celebrity.category,
        follower_count=celebrity.follower_count,
        is_active=celebrity.is_active,
        scrape_priority=celebrity.scrape_priority,
        discovered_at=celebrity.discovered_at,
        last_scraped_at=celebrity.last_scraped_at,
        post_count=post_count,
    )


@router.delete("/{celebrity_id}", status_code=204)
async def delete_celebrity(
    celebrity_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a celebrity and all associated data."""
    result = await db.execute(select(Celebrity).where(Celebrity.id == celebrity_id))
    celebrity = result.scalar_one_or_none()

    if not celebrity:
        raise HTTPException(status_code=404, detail="Celebrity not found")

    await db.delete(celebrity)
    await db.commit()
