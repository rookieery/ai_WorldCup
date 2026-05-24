"""Team API routes — GET /api/teams, GET /api/teams/:code."""

from __future__ import annotations

from typing import AsyncGenerator

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.common import ApiResponse, PaginatedResponse

router = APIRouter(prefix="/api/teams", tags=["teams"])


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


@router.get("", summary="List all teams")
async def list_teams(
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=100, ge=1, le=100, description="Items per page"),
    group: str | None = Query(default=None, max_length=1, description="Filter by group (A-L)"),
    lang: str = Query(default="en", description="Language: en or zh"),
    session: AsyncSession = Depends(_get_db),
) -> ApiResponse[PaginatedResponse]:
    """Return a paginated list of teams, optionally filtered by group."""
    from app.services.team_service import TeamService

    svc = TeamService(session)
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


@router.get("/{code}", summary="Get team detail by code")
async def get_team_by_code(
    code: str,
    lang: str = Query(default="en", description="Language: en or zh"),
    session: AsyncSession = Depends(_get_db),
) -> ApiResponse:
    """Return a single team identified by its 3-letter code."""
    from app.services.team_service import TeamService

    svc = TeamService(session)
    team_vo = await svc.get_team_by_code(code, lang=lang)
    return ApiResponse(data=team_vo)
