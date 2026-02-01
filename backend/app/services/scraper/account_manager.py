"""Account manager for Instagram scraper accounts."""

import logging
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models import ScraperAccount
from app.config import settings

logger = logging.getLogger(__name__)


class AccountManager:
    """
    Manages multiple scraper accounts for rotation and quota management.

    Features:
    - Get available account with remaining quota
    - Track request counts per account
    - Mark accounts as banned
    - Rotate to next available account
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_available_account(self) -> Optional[ScraperAccount]:
        """
        Get an available scraper account with remaining quota.

        Returns the account with:
        - is_active = True
        - is_banned = False
        - requests_today < daily limit

        Returns:
            ScraperAccount or None if no accounts available
        """
        daily_limit = settings.requests_per_account_per_day

        result = await self.db.execute(
            select(ScraperAccount)
            .where(ScraperAccount.is_active == True)
            .where(ScraperAccount.is_banned == False)
            .where(ScraperAccount.requests_today < daily_limit)
            .order_by(ScraperAccount.requests_today.asc())  # Prefer least-used account
            .limit(1)
        )

        account = result.scalar_one_or_none()

        if account:
            logger.debug(
                f"Selected account @{account.username} "
                f"({account.requests_today}/{daily_limit} requests today)"
            )
        else:
            logger.warning("No available scraper accounts with remaining quota")

        return account

    async def mark_account_used(
        self,
        account_id: UUID,
        increment: int = 1,
    ) -> bool:
        """
        Increment request counter for an account.

        Args:
            account_id: UUID of the scraper account
            increment: Number of requests to add (default 1)

        Returns:
            True if successful, False otherwise
        """
        try:
            result = await self.db.execute(
                select(ScraperAccount).where(ScraperAccount.id == account_id)
            )
            account = result.scalar_one_or_none()

            if not account:
                logger.warning(f"Account {account_id} not found")
                return False

            account.requests_today += increment
            account.last_used_at = datetime.utcnow()
            await self.db.commit()

            logger.debug(
                f"Updated @{account.username}: {account.requests_today} requests today"
            )
            return True

        except Exception as e:
            logger.error(f"Error updating account {account_id}: {e}")
            await self.db.rollback()
            return False

    async def mark_account_banned(
        self,
        account_id: UUID,
        reason: Optional[str] = None,
    ) -> bool:
        """
        Mark an account as banned.

        Args:
            account_id: UUID of the scraper account
            reason: Optional reason for the ban

        Returns:
            True if successful, False otherwise
        """
        try:
            result = await self.db.execute(
                select(ScraperAccount).where(ScraperAccount.id == account_id)
            )
            account = result.scalar_one_or_none()

            if not account:
                logger.warning(f"Account {account_id} not found")
                return False

            account.is_banned = True
            account.banned_at = datetime.utcnow()
            account.is_active = False
            await self.db.commit()

            logger.warning(
                f"Account @{account.username} marked as banned"
                + (f": {reason}" if reason else "")
            )
            return True

        except Exception as e:
            logger.error(f"Error marking account {account_id} as banned: {e}")
            await self.db.rollback()
            return False

    async def rotate_account(
        self,
        current_account_id: Optional[UUID] = None,
    ) -> Optional[ScraperAccount]:
        """
        Get the next available account, excluding the current one.

        Args:
            current_account_id: UUID of the current account to exclude

        Returns:
            Next available ScraperAccount or None
        """
        daily_limit = settings.requests_per_account_per_day

        query = (
            select(ScraperAccount)
            .where(ScraperAccount.is_active == True)
            .where(ScraperAccount.is_banned == False)
            .where(ScraperAccount.requests_today < daily_limit)
            .order_by(ScraperAccount.requests_today.asc())
        )

        if current_account_id:
            query = query.where(ScraperAccount.id != current_account_id)

        result = await self.db.execute(query.limit(1))
        account = result.scalar_one_or_none()

        if account:
            logger.info(
                f"Rotated to account @{account.username} "
                f"({account.requests_today}/{daily_limit} requests)"
            )
        else:
            logger.warning("No accounts available for rotation")

        return account

    async def get_all_accounts(self, active_only: bool = True) -> List[ScraperAccount]:
        """
        Get all scraper accounts.

        Args:
            active_only: Only return active, non-banned accounts

        Returns:
            List of ScraperAccount objects
        """
        query = select(ScraperAccount)

        if active_only:
            query = query.where(
                ScraperAccount.is_active == True,
                ScraperAccount.is_banned == False,
            )

        result = await self.db.execute(query.order_by(ScraperAccount.username))
        return list(result.scalars().all())

    async def get_account_stats(self) -> dict:
        """
        Get statistics about all scraper accounts.

        Returns:
            Dict with account statistics
        """
        all_accounts = await self.get_all_accounts(active_only=False)
        active_accounts = [a for a in all_accounts if a.is_active and not a.is_banned]
        banned_accounts = [a for a in all_accounts if a.is_banned]

        total_requests = sum(a.requests_today for a in active_accounts)
        total_capacity = len(active_accounts) * settings.requests_per_account_per_day
        remaining_capacity = total_capacity - total_requests

        return {
            "total_accounts": len(all_accounts),
            "active_accounts": len(active_accounts),
            "banned_accounts": len(banned_accounts),
            "total_requests_today": total_requests,
            "remaining_capacity": remaining_capacity,
            "accounts": [
                {
                    "username": a.username,
                    "is_active": a.is_active,
                    "is_banned": a.is_banned,
                    "requests_today": a.requests_today,
                    "last_used_at": a.last_used_at.isoformat() if a.last_used_at else None,
                }
                for a in all_accounts
            ],
        }

    async def reset_daily_counters(self) -> int:
        """
        Reset daily request counters for all accounts.

        Returns:
            Number of accounts reset
        """
        try:
            result = await self.db.execute(
                update(ScraperAccount)
                .where(ScraperAccount.requests_today > 0)
                .values(requests_today=0)
            )
            await self.db.commit()

            count = result.rowcount
            logger.info(f"Reset daily counters for {count} accounts")
            return count

        except Exception as e:
            logger.error(f"Error resetting daily counters: {e}")
            await self.db.rollback()
            return 0

    async def reactivate_account(
        self,
        account_id: UUID,
    ) -> bool:
        """
        Reactivate a previously banned or deactivated account.

        Args:
            account_id: UUID of the account to reactivate

        Returns:
            True if successful, False otherwise
        """
        try:
            result = await self.db.execute(
                select(ScraperAccount).where(ScraperAccount.id == account_id)
            )
            account = result.scalar_one_or_none()

            if not account:
                logger.warning(f"Account {account_id} not found")
                return False

            account.is_active = True
            account.is_banned = False
            account.banned_at = None
            account.requests_today = 0
            await self.db.commit()

            logger.info(f"Reactivated account @{account.username}")
            return True

        except Exception as e:
            logger.error(f"Error reactivating account {account_id}: {e}")
            await self.db.rollback()
            return False


class SyncAccountManager:
    """
    Synchronous version of AccountManager for use in Celery tasks.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_available_account(self) -> Optional[ScraperAccount]:
        """Get an available scraper account with remaining quota."""
        daily_limit = settings.requests_per_account_per_day

        account = (
            self.db.query(ScraperAccount)
            .filter(ScraperAccount.is_active == True)
            .filter(ScraperAccount.is_banned == False)
            .filter(ScraperAccount.requests_today < daily_limit)
            .order_by(ScraperAccount.requests_today.asc())
            .first()
        )

        if account:
            logger.debug(
                f"Selected account @{account.username} "
                f"({account.requests_today}/{daily_limit} requests today)"
            )
        else:
            logger.warning("No available scraper accounts with remaining quota")

        return account

    def mark_account_used(self, account_id: UUID, increment: int = 1) -> bool:
        """Increment request counter for an account."""
        try:
            account = (
                self.db.query(ScraperAccount)
                .filter(ScraperAccount.id == account_id)
                .first()
            )

            if not account:
                return False

            account.requests_today += increment
            account.last_used_at = datetime.utcnow()
            self.db.commit()
            return True

        except Exception as e:
            logger.error(f"Error updating account {account_id}: {e}")
            self.db.rollback()
            return False

    def mark_account_banned(self, account_id: UUID, reason: Optional[str] = None) -> bool:
        """Mark an account as banned."""
        try:
            account = (
                self.db.query(ScraperAccount)
                .filter(ScraperAccount.id == account_id)
                .first()
            )

            if not account:
                return False

            account.is_banned = True
            account.banned_at = datetime.utcnow()
            account.is_active = False
            self.db.commit()

            logger.warning(
                f"Account @{account.username} marked as banned"
                + (f": {reason}" if reason else "")
            )
            return True

        except Exception as e:
            logger.error(f"Error marking account {account_id} as banned: {e}")
            self.db.rollback()
            return False

    def rotate_account(self, current_account_id: Optional[UUID] = None) -> Optional[ScraperAccount]:
        """Get the next available account, excluding the current one."""
        daily_limit = settings.requests_per_account_per_day

        query = (
            self.db.query(ScraperAccount)
            .filter(ScraperAccount.is_active == True)
            .filter(ScraperAccount.is_banned == False)
            .filter(ScraperAccount.requests_today < daily_limit)
        )

        if current_account_id:
            query = query.filter(ScraperAccount.id != current_account_id)

        return query.order_by(ScraperAccount.requests_today.asc()).first()
