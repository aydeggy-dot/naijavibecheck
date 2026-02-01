"""
Celebrity Discovery API Routes

Endpoints for:
- Running discovery jobs (trending, blog scraping)
- Submitting celebrity suggestions
- Admin approval workflow
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.services.discovery import TrendingMonitor, BlogScraper, CelebritySuggester

router = APIRouter()


# ============================================
# Request/Response Models
# ============================================

class SuggestionSubmit(BaseModel):
    """Request model for submitting a celebrity suggestion."""
    instagram_username: str
    full_name: Optional[str] = None
    category: Optional[str] = None
    reason: Optional[str] = None
    example_post_url: Optional[str] = None


class SuggestionApprove(BaseModel):
    """Request model for approving a suggestion."""
    scrape_priority: int = 5


class SuggestionReject(BaseModel):
    """Request model for rejecting a suggestion."""
    reason: Optional[str] = None


# ============================================
# Discovery Endpoints
# ============================================

@router.post("/trending/run")
async def run_trending_discovery(
    background_tasks: BackgroundTasks,
):
    """
    Run trending hashtag/topic discovery.

    Checks Twitter, Google Trends for Nigerian trending topics
    and extracts celebrity mentions.
    """
    async def run_discovery():
        monitor = TrendingMonitor()
        try:
            return await monitor.discover_trending_celebrities()
        finally:
            await monitor.close()

    # Run in background for large operations
    # For now, run synchronously for demo
    monitor = TrendingMonitor()
    try:
        celebrities = await monitor.discover_trending_celebrities()

        return {
            "status": "completed",
            "discovered": len(celebrities),
            "celebrities": celebrities[:20],  # Top 20
            "sources": ["twitter", "google"]
        }
    finally:
        await monitor.close()


@router.get("/trending/celebrities")
async def get_trending_celebrities():
    """
    Get currently trending celebrities from cached discovery results.
    """
    monitor = TrendingMonitor()
    try:
        celebrities = await monitor.discover_trending_celebrities()

        # Filter high confidence
        high_confidence = [c for c in celebrities if c.get("confidence", 0) >= 0.7]

        return {
            "trending": high_confidence[:15],
            "total": len(high_confidence)
        }
    finally:
        await monitor.close()


@router.post("/blogs/scrape")
async def run_blog_scraper():
    """
    Scrape Nigerian entertainment blogs for celebrity mentions.

    Sources: Linda Ikeji, Bella Naija, Pulse Nigeria, The Net NG
    """
    scraper = BlogScraper()
    try:
        celebrities = await scraper.discover_from_blogs()

        return {
            "status": "completed",
            "discovered": len(celebrities),
            "celebrities": celebrities[:20],
            "sources": [s["name"] for s in BlogScraper.SOURCES]
        }
    finally:
        await scraper.close()


@router.get("/blogs/trending")
async def get_blog_trending():
    """
    Get celebrities trending in Nigerian blogs.
    """
    scraper = BlogScraper()
    try:
        celebrities = await scraper.discover_from_blogs()

        return {
            "trending": celebrities[:15],
            "total": len(celebrities)
        }
    finally:
        await scraper.close()


# ============================================
# Suggestion Endpoints
# ============================================

@router.post("/suggestions")
async def submit_suggestion(
    data: SuggestionSubmit,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a celebrity suggestion.

    Anyone can suggest a celebrity to track.
    Suggestions go through admin approval.
    """
    suggester = CelebritySuggester(db)

    result = await suggester.submit_suggestion(
        instagram_username=data.instagram_username,
        full_name=data.full_name,
        category=data.category,
        reason=data.reason,
        post_url=data.example_post_url,
    )

    return result


@router.get("/suggestions")
async def get_suggestions(
    status: str = "pending",
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """
    Get celebrity suggestions.

    Args:
        status: Filter by status (pending, approved, rejected, all)
        limit: Max results to return
    """
    from sqlalchemy import select
    from app.models.celebrity import CelebritySuggestion

    query = select(CelebritySuggestion)

    if status != "all":
        query = query.where(CelebritySuggestion.status == status)

    query = query.order_by(
        CelebritySuggestion.vote_count.desc(),
        CelebritySuggestion.submitted_at.desc()
    ).limit(limit)

    result = await db.execute(query)
    suggestions = result.scalars().all()

    return {
        "suggestions": [
            {
                "id": str(s.id),
                "instagram_username": s.instagram_username,
                "full_name": s.full_name,
                "category": s.category,
                "reason": s.reason,
                "submitted_by": s.submitted_by,
                "example_post_url": s.example_post_url,
                "status": s.status,
                "vote_count": s.vote_count or 0,
                "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
            }
            for s in suggestions
        ],
        "count": len(suggestions)
    }


@router.post("/suggestions/{suggestion_id}/approve")
async def approve_suggestion(
    suggestion_id: UUID,
    data: SuggestionApprove,
    db: AsyncSession = Depends(get_db),
):
    """
    Approve a celebrity suggestion (admin only).

    Creates the celebrity and starts tracking.
    """
    suggester = CelebritySuggester(db)

    result = await suggester.approve_suggestion(
        suggestion_id=str(suggestion_id),
        approved_by="admin",  # TODO: Get from auth
        scrape_priority=data.scrape_priority
    )

    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))

    return result


@router.post("/suggestions/{suggestion_id}/reject")
async def reject_suggestion(
    suggestion_id: UUID,
    data: SuggestionReject,
    db: AsyncSession = Depends(get_db),
):
    """
    Reject a celebrity suggestion (admin only).
    """
    suggester = CelebritySuggester(db)

    result = await suggester.reject_suggestion(
        suggestion_id=str(suggestion_id),
        rejected_by="admin",  # TODO: Get from auth
        reason=data.reason
    )

    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))

    return result


@router.post("/suggestions/{suggestion_id}/upvote")
async def upvote_suggestion(
    suggestion_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Upvote a suggestion to increase its priority.

    More votes = higher priority for admin review.
    """
    suggester = CelebritySuggester(db)

    result = await suggester.upvote_suggestion(
        suggestion_id=str(suggestion_id)
    )

    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))

    return result


@router.get("/suggestions/stats")
async def get_suggestion_stats(
    db: AsyncSession = Depends(get_db),
):
    """Get suggestion statistics."""
    suggester = CelebritySuggester(db)
    return await suggester.get_suggestion_stats()


# ============================================
# Combined Discovery Endpoint
# ============================================

@router.post("/run-all")
async def run_full_discovery():
    """
    Run all discovery methods and combine results.

    This is the main discovery endpoint that:
    1. Checks trending topics (Twitter, Google)
    2. Scrapes entertainment blogs
    3. Combines and deduplicates results
    """
    results = {
        "trending": [],
        "blogs": [],
        "combined": [],
        "errors": []
    }

    # Run trending discovery
    try:
        monitor = TrendingMonitor()
        trending = await monitor.discover_trending_celebrities()
        results["trending"] = trending[:10]
        await monitor.close()
    except Exception as e:
        results["errors"].append(f"Trending: {str(e)}")

    # Run blog scraping
    try:
        scraper = BlogScraper()
        blogs = await scraper.discover_from_blogs()
        results["blogs"] = blogs[:10]
        await scraper.close()
    except Exception as e:
        results["errors"].append(f"Blogs: {str(e)}")

    # Combine and deduplicate
    seen = set()
    combined = []

    for celeb in results["trending"] + results["blogs"]:
        name = celeb.get("name", "").lower()
        if name and name not in seen:
            seen.add(name)
            combined.append(celeb)

    # Sort by confidence/mention count
    combined.sort(
        key=lambda x: x.get("confidence", 0) + x.get("mention_count", 0) * 0.1,
        reverse=True
    )

    results["combined"] = combined[:20]

    return {
        "status": "completed",
        "total_discovered": len(combined),
        "results": results
    }
