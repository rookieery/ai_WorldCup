"""Match API routes — GET /api/matches, GET /api/matches/live, GET /api/matches/:id."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_db, get_match_service
from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.match_schema import MatchQueryParams
from app.services.match_service import MatchService

router = APIRouter(prefix="/api/matches", tags=["matches"])


# ── routes ──────────────────────────────────────────────────────────────────


@router.get("", summary="List matches with filters")
async def list_matches(
    date: str | None = Query(default=None, description="Filter by date (YYYY-MM-DD)"),
    stage: str | None = Query(
        default=None, description="Filter by stage (group / R32 / R16 / QF / SF / 3rd / F)"
    ),
    group: str | None = Query(
        default=None, max_length=1, description="Filter by group (A-L)"
    ),
    team: str | None = Query(
        default=None, max_length=3, description="Filter by team code"
    ),
    status: str | None = Query(
        default=None, description="Filter by status (upcoming / live / finished / postponed)"
    ),
    timezone: str | None = Query(
        default=None, description="Target IANA timezone for local_time conversion"
    ),
    lang: str = Query(default="en", description="Language: en or zh"),
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    svc: MatchService = Depends(get_match_service),
) -> ApiResponse[PaginatedResponse]:
    """Return a paginated list of matches with optional filters."""
    params = MatchQueryParams(date=date, stage=stage, group=group, team=team, status=status)
    items, total = await svc.get_matches(
        params=params,
        timezone_name=timezone,
        lang=lang,
        page=page,
        page_size=page_size,
    )
    paginated = PaginatedResponse(items=items, total=total, page=page, page_size=page_size)
    return ApiResponse(data=paginated)


@router.get("/live", summary="Get live matches")
async def get_live_matches(
    timezone: str | None = Query(
        default=None, description="Target IANA timezone for local_time conversion"
    ),
    lang: str = Query(default="en", description="Language: en or zh"),
    svc: MatchService = Depends(get_match_service),
) -> ApiResponse:
    """Return all currently live matches."""
    items = await svc.get_live_matches(timezone_name=timezone, lang=lang)
    return ApiResponse(data=items)


@router.get("/{match_id}", summary="Get match detail by ID")
async def get_match_by_id(
    match_id: int,
    timezone: str | None = Query(
        default=None, description="Target IANA timezone for local_time conversion"
    ),
    lang: str = Query(default="en", description="Language: en or zh"),
    svc: MatchService = Depends(get_match_service),
) -> ApiResponse:
    """Return a single match with its events."""
    match_vo = await svc.get_match_by_id(match_id, timezone_name=timezone, lang=lang)
    return ApiResponse(data=match_vo)
