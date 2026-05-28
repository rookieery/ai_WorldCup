"""Team API routes — GET /api/teams, GET /api/teams/:code, GET /api/teams/:code/stats."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_team_service
from app.schemas.common import ApiResponse, PaginatedResponse
from app.services.team_service import TeamService

router = APIRouter(prefix="/api/teams", tags=["teams"])


# ── routes ──────────────────────────────────────────────────────────────────


@router.get("", summary="List all teams")
async def list_teams(
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=100, ge=1, le=100, description="Items per page"),
    group: str | None = Query(default=None, max_length=1, description="Filter by group (A-L)"),
    lang: str = Query(default="en", description="Language: en or zh"),
    svc: TeamService = Depends(get_team_service),
) -> ApiResponse[PaginatedResponse]:
    """Return a paginated list of teams, optionally filtered by group."""
    items, total = await svc.get_all_teams(
        page=page,
        page_size=page_size,
        group=group,
        lang=lang,
    )
    paginated = PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )
    return ApiResponse(data=paginated)


@router.get("/{code}/stats", summary="Get team stats by code")
async def get_team_stats(
    code: str,
    timezone: str | None = Query(
        default=None, description="Target IANA timezone for local_time conversion"
    ),
    lang: str = Query(default="en", description="Language: en or zh"),
    svc: TeamService = Depends(get_team_service),
) -> ApiResponse:
    """Return comprehensive statistics for a team identified by its 3-letter code.

    Includes team info, group standing, finished matches, and upcoming matches.
    """
    stats_vo = await svc.get_team_stats(code, lang=lang, timezone_name=timezone)
    return ApiResponse(data=stats_vo)


@router.get("/{code}", summary="Get team detail by code")
async def get_team_by_code(
    code: str,
    lang: str = Query(default="en", description="Language: en or zh"),
    svc: TeamService = Depends(get_team_service),
) -> ApiResponse:
    """Return a single team identified by its 3-letter code."""
    team_vo = await svc.get_team_by_code(code, lang=lang)
    return ApiResponse(data=team_vo)
