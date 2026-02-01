"""
Celebrity Suggestion System

Handles user-submitted celebrity suggestions with admin approval workflow.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import uuid4
from enum import Enum

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class SuggestionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"


class CelebritySuggester:
    """
    Manages user-submitted celebrity suggestions.

    Features:
    - Submit new celebrity suggestions
    - Admin approval workflow
    - Duplicate detection
    - Auto-verification via Instagram
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def submit_suggestion(
        self,
        instagram_username: str,
        full_name: Optional[str] = None,
        category: Optional[str] = None,
        reason: Optional[str] = None,
        submitted_by: Optional[str] = None,
        post_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Submit a new celebrity suggestion.

        Args:
            instagram_username: Instagram handle (required)
            full_name: Celebrity's full name
            category: Category (musician, actor, comedian, influencer)
            reason: Why this celebrity should be tracked
            submitted_by: User ID or email of submitter
            post_url: Example post URL that prompted the suggestion

        Returns:
            Submission result with suggestion_id
        """
        from app.models.celebrity import Celebrity, CelebritySuggestion

        # Normalize username
        username = instagram_username.lower().strip().replace("@", "")

        # Check if celebrity already exists
        existing = await self.db.execute(
            select(Celebrity).where(Celebrity.instagram_username == username)
        )
        if existing.scalar_one_or_none():
            return {
                "status": "duplicate",
                "message": f"Celebrity @{username} is already being tracked",
                "instagram_username": username
            }

        # Check if suggestion already exists
        existing_suggestion = await self.db.execute(
            select(CelebritySuggestion).where(
                CelebritySuggestion.instagram_username == username,
                CelebritySuggestion.status == SuggestionStatus.PENDING
            )
        )
        if existing_suggestion.scalar_one_or_none():
            return {
                "status": "already_submitted",
                "message": f"@{username} has already been suggested and is pending review",
                "instagram_username": username
            }

        # Create new suggestion
        suggestion = CelebritySuggestion(
            id=uuid4(),
            instagram_username=username,
            full_name=full_name,
            category=category or "unknown",
            reason=reason,
            submitted_by=submitted_by,
            example_post_url=post_url,
            status=SuggestionStatus.PENDING,
            submitted_at=datetime.utcnow()
        )

        self.db.add(suggestion)
        await self.db.commit()
        await self.db.refresh(suggestion)

        logger.info(f"New celebrity suggestion: @{username} by {submitted_by}")

        return {
            "status": "submitted",
            "message": f"Thanks! @{username} has been submitted for review",
            "suggestion_id": str(suggestion.id),
            "instagram_username": username
        }

    async def get_pending_suggestions(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get all pending suggestions for admin review."""
        from app.models.celebrity import CelebritySuggestion

        result = await self.db.execute(
            select(CelebritySuggestion)
            .where(CelebritySuggestion.status == SuggestionStatus.PENDING)
            .order_by(CelebritySuggestion.submitted_at.desc())
            .offset(offset)
            .limit(limit)
        )
        suggestions = result.scalars().all()

        return [
            {
                "id": str(s.id),
                "instagram_username": s.instagram_username,
                "full_name": s.full_name,
                "category": s.category,
                "reason": s.reason,
                "submitted_by": s.submitted_by,
                "example_post_url": s.example_post_url,
                "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
                "vote_count": s.vote_count or 0
            }
            for s in suggestions
        ]

    async def approve_suggestion(
        self,
        suggestion_id: str,
        approved_by: str,
        scrape_priority: int = 5
    ) -> Dict[str, Any]:
        """
        Approve a suggestion and create the celebrity.

        Args:
            suggestion_id: UUID of the suggestion
            approved_by: Admin user who approved
            scrape_priority: Priority for scraping (1-10)

        Returns:
            Result with new celebrity_id
        """
        from app.models.celebrity import Celebrity, CelebritySuggestion

        # Get suggestion
        result = await self.db.execute(
            select(CelebritySuggestion).where(CelebritySuggestion.id == suggestion_id)
        )
        suggestion = result.scalar_one_or_none()

        if not suggestion:
            return {"status": "error", "message": "Suggestion not found"}

        if suggestion.status != SuggestionStatus.PENDING:
            return {"status": "error", "message": f"Suggestion already {suggestion.status}"}

        # Create celebrity
        celebrity = Celebrity(
            id=uuid4(),
            instagram_username=suggestion.instagram_username,
            full_name=suggestion.full_name or suggestion.instagram_username,
            category=suggestion.category,
            is_active=True,
            scrape_priority=scrape_priority,
            metadata={
                "source": "user_suggestion",
                "suggested_by": suggestion.submitted_by,
                "reason": suggestion.reason
            }
        )

        self.db.add(celebrity)

        # Update suggestion status
        suggestion.status = SuggestionStatus.APPROVED
        suggestion.reviewed_by = approved_by
        suggestion.reviewed_at = datetime.utcnow()

        await self.db.commit()

        logger.info(f"Approved celebrity: @{celebrity.instagram_username}")

        return {
            "status": "approved",
            "message": f"@{celebrity.instagram_username} is now being tracked",
            "celebrity_id": str(celebrity.id),
            "instagram_username": celebrity.instagram_username
        }

    async def reject_suggestion(
        self,
        suggestion_id: str,
        rejected_by: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Reject a suggestion."""
        from app.models.celebrity import CelebritySuggestion

        result = await self.db.execute(
            select(CelebritySuggestion).where(CelebritySuggestion.id == suggestion_id)
        )
        suggestion = result.scalar_one_or_none()

        if not suggestion:
            return {"status": "error", "message": "Suggestion not found"}

        suggestion.status = SuggestionStatus.REJECTED
        suggestion.reviewed_by = rejected_by
        suggestion.reviewed_at = datetime.utcnow()
        suggestion.rejection_reason = reason

        await self.db.commit()

        return {
            "status": "rejected",
            "message": f"Suggestion for @{suggestion.instagram_username} rejected",
            "instagram_username": suggestion.instagram_username
        }

    async def upvote_suggestion(
        self,
        suggestion_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upvote a suggestion to increase its priority.

        More votes = higher priority for admin review.
        """
        from app.models.celebrity import CelebritySuggestion

        result = await self.db.execute(
            select(CelebritySuggestion).where(CelebritySuggestion.id == suggestion_id)
        )
        suggestion = result.scalar_one_or_none()

        if not suggestion:
            return {"status": "error", "message": "Suggestion not found"}

        if suggestion.status != SuggestionStatus.PENDING:
            return {"status": "error", "message": "Can only vote on pending suggestions"}

        suggestion.vote_count = (suggestion.vote_count or 0) + 1
        await self.db.commit()

        return {
            "status": "voted",
            "vote_count": suggestion.vote_count,
            "instagram_username": suggestion.instagram_username
        }

    async def get_suggestion_stats(self) -> Dict[str, Any]:
        """Get statistics about suggestions."""
        from app.models.celebrity import CelebritySuggestion

        # Count by status
        result = await self.db.execute(
            select(
                CelebritySuggestion.status,
                func.count(CelebritySuggestion.id)
            ).group_by(CelebritySuggestion.status)
        )
        status_counts = dict(result.all())

        return {
            "pending": status_counts.get(SuggestionStatus.PENDING, 0),
            "approved": status_counts.get(SuggestionStatus.APPROVED, 0),
            "rejected": status_counts.get(SuggestionStatus.REJECTED, 0),
            "total": sum(status_counts.values())
        }


# Convenience functions for API routes
async def submit_celebrity_suggestion(
    db: AsyncSession,
    instagram_username: str,
    **kwargs
) -> Dict[str, Any]:
    """Submit a celebrity suggestion."""
    suggester = CelebritySuggester(db)
    return await suggester.submit_suggestion(instagram_username, **kwargs)


async def get_pending_suggestions(
    db: AsyncSession,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Get pending suggestions."""
    suggester = CelebritySuggester(db)
    return await suggester.get_pending_suggestions(limit=limit)


async def approve_celebrity(
    db: AsyncSession,
    suggestion_id: str,
    approved_by: str
) -> Dict[str, Any]:
    """Approve a celebrity suggestion."""
    suggester = CelebritySuggester(db)
    return await suggester.approve_suggestion(suggestion_id, approved_by)
