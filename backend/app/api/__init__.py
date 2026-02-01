"""API routes for NaijaVibeCheck."""

from fastapi import APIRouter

from app.api.routes import (
    celebrities,
    posts,
    analytics,
    content,
    settings,
    health,
    analysis,
    generate,
    publish,
    discovery,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(celebrities.router, prefix="/celebrities", tags=["celebrities"])
api_router.include_router(posts.router, prefix="/posts", tags=["posts"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
api_router.include_router(generate.router, prefix="/generate", tags=["generate"])
api_router.include_router(publish.router, prefix="/publish", tags=["publish"])
api_router.include_router(content.router, prefix="/content", tags=["content"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(discovery.router, prefix="/discovery", tags=["discovery"])
