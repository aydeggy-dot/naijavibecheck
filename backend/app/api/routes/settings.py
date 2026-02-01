"""Settings API endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models import Settings as SettingsModel, ScraperAccount, Proxy

router = APIRouter()


class SettingValue(BaseModel):
    """Schema for setting value."""
    value: Any


@router.get("")
async def get_all_settings(db: AsyncSession = Depends(get_db)):
    """Get all system settings."""
    result = await db.execute(select(SettingsModel))
    settings = result.scalars().all()

    return {s.key: s.value for s in settings}


@router.get("/{key}")
async def get_setting(key: str, db: AsyncSession = Depends(get_db)):
    """Get a specific setting by key."""
    result = await db.execute(
        select(SettingsModel).where(SettingsModel.key == key)
    )
    setting = result.scalar_one_or_none()

    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")

    return {"key": setting.key, "value": setting.value}


@router.put("/{key}")
async def set_setting(
    key: str,
    data: SettingValue,
    db: AsyncSession = Depends(get_db),
):
    """Set a system setting."""
    result = await db.execute(
        select(SettingsModel).where(SettingsModel.key == key)
    )
    setting = result.scalar_one_or_none()

    if setting:
        setting.value = data.value
    else:
        setting = SettingsModel(key=key, value=data.value)
        db.add(setting)

    await db.commit()
    await db.refresh(setting)

    return {"key": setting.key, "value": setting.value}


@router.get("/scraper/accounts")
async def list_scraper_accounts(db: AsyncSession = Depends(get_db)):
    """List all scraper accounts (without passwords)."""
    result = await db.execute(
        select(ScraperAccount).order_by(ScraperAccount.created_at.desc())
    )
    accounts = result.scalars().all()

    return [
        {
            "id": a.id,
            "username": a.username,
            "is_active": a.is_active,
            "last_used_at": a.last_used_at,
            "requests_today": a.requests_today,
            "is_banned": a.is_banned,
            "banned_at": a.banned_at,
            "created_at": a.created_at,
        }
        for a in accounts
    ]


@router.get("/scraper/proxies")
async def list_proxies(db: AsyncSession = Depends(get_db)):
    """List all configured proxies (without passwords)."""
    result = await db.execute(
        select(Proxy).order_by(Proxy.created_at.desc())
    )
    proxies = result.scalars().all()

    return [
        {
            "id": p.id,
            "host": p.host,
            "port": p.port,
            "protocol": p.protocol,
            "is_active": p.is_active,
            "last_used_at": p.last_used_at,
            "failure_count": p.failure_count,
            "country_code": p.country_code,
            "created_at": p.created_at,
        }
        for p in proxies
    ]
