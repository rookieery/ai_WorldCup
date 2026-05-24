"""Match API routes — GET /api/matches, GET /api/matches/live, GET /api/matches/:id."""

from __future__ import annotations

from typing import AsyncGenerator

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.match_schema import MatchQueryParams

router = APIRouter(prefix="/api/matches", tags=["matches"])


# ── session helper (P1-11 will centralise this into app/dependencies.py) ──


async def _get_db() -> AsyncGenerator[AsyncSession, None]:
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.orm import sessionmaker

    from app.config import settings

    engine = create_async_engine(settings.DATABASE_URL, echo=settings.is_development)
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session


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
    session: AsyncSession = Depends(_get_db),
) -> ApiResponse[PaginatedResponse]:
    """Return a paginated list of matches with optional filters."""
    from app.services.match_service import MatchService

    params = MatchQueryParams(date=date, stage=stage, group=group, team=team, status=status)
    svc = MatchService(session)
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
    session: AsyncSession = Depends(_get_db),
) -> ApiResponse:
    """Return all currently live matches."""
    from app.services.match_service import MatchService

    svc = MatchService(session)
    items = await svc.get_live_matches(timezone_name=timezone, lang=lang)
    return ApiResponse(data=items)


@router.get("/{match_id}", summary="Get match detail by ID")
async def get_match_by_id(
    match_id: int,
    timezone: str | None = Query(
        default=None, description="Target IANA timezone for local_time conversion"
    ),
    lang: str = Query(default="en", description="Language: en or zh"),
    session: AsyncSession = Depends(_get_db),
) -> ApiResponse:
    """Return a single match with its events."""
    from app.services.match_service import MatchService

    svc = MatchService(session)
    match_vo = await svc.get_match_by_id(match_id, timezone_name=timezone, lang=lang)
    return ApiResponse(data=match_vo)
