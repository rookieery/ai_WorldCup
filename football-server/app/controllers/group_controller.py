"""Group API routes — GET /api/groups, GET /api/groups/:group."""

from __future__ import annotations

from typing import AsyncGenerator

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.common import ApiResponse

router = APIRouter(prefix="/api/groups", tags=["groups"])


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


@router.get("", summary="List all 12 groups with standings")
async def list_groups(
    lang: str = Query(default="en", description="Language: en or zh"),
    session: AsyncSession = Depends(_get_db),
) -> ApiResponse:
    """Return standings overview for all 12 groups (A-L).

    Each group contains its standings sorted by points desc,
    goal_difference desc, goals_for desc.
    """
    from app.services.group_service import GroupService

    svc = GroupService(session)
    groups = await svc.get_all_groups(lang=lang)
    return ApiResponse(data=groups)


@router.get("/{group}", summary="Get single group detail (A-L)")
async def get_group_detail(
    group: str,
    timezone: str | None = Query(
        default=None, description="Target IANA timezone for local_time conversion"
    ),
    lang: str = Query(default="en", description="Language: en or zh"),
    session: AsyncSession = Depends(_get_db),
) -> ApiResponse:
    """Return standings + matches for a single group.

    ``group`` must be a single letter from A to L.
    """
    from app.services.group_service import GroupService

    svc = GroupService(session)
    detail = await svc.get_group_detail(
        group,
        timezone_name=timezone,
        lang=lang,
    )
    return ApiResponse(data=detail)
