"""Pydantic schemas for NaijaVibeCheck API."""

from app.schemas.celebrity import (
    CelebrityBase,
    CelebrityCreate,
    CelebrityUpdate,
    CelebrityResponse,
    CelebrityListResponse,
)
from app.schemas.post import (
    PostBase,
    PostCreate,
    PostResponse,
    PostListResponse,
)
from app.schemas.comment import (
    CommentBase,
    CommentResponse,
    CommentWithAnalysis,
)
from app.schemas.analysis import (
    CommentAnalysisResponse,
    PostAnalysisResponse,
    AnalysisStats,
)
from app.schemas.content import (
    GeneratedContentBase,
    GeneratedContentCreate,
    GeneratedContentUpdate,
    GeneratedContentResponse,
    ContentStatus,
)

__all__ = [
    # Celebrity
    "CelebrityBase",
    "CelebrityCreate",
    "CelebrityUpdate",
    "CelebrityResponse",
    "CelebrityListResponse",
    # Post
    "PostBase",
    "PostCreate",
    "PostResponse",
    "PostListResponse",
    # Comment
    "CommentBase",
    "CommentResponse",
    "CommentWithAnalysis",
    # Analysis
    "CommentAnalysisResponse",
    "PostAnalysisResponse",
    "AnalysisStats",
    # Content
    "GeneratedContentBase",
    "GeneratedContentCreate",
    "GeneratedContentUpdate",
    "GeneratedContentResponse",
    "ContentStatus",
]
