"""Stats API routes — GET /api/stats/scorers."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.common import ApiResponse
from app.services.stats_service import StatsService

router = APIRouter(prefix="/api/stats", tags=["stats"])


def _get_stats_service(session: AsyncSession = Depends(get_db)) -> StatsService:
    """Create a ``StatsService`` with an injected session."""
    return StatsService(session)


@router.get("/scorers", summary="Get scorer leaderboard")
async def get_scorers(
    lang: str = Query(default="en", description="Language: en or zh"),
    limit: int = Query(default=50, ge=1, le=100, description="Max number of scorers"),
    svc: StatsService = Depends(_get_stats_service),
) -> ApiResponse:
    """Return the top scorers leaderboard with goals and assists."""
    items = await svc.get_scorers(lang=lang, limit=limit)
    return ApiResponse(data=items)
