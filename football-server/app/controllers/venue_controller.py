"""Venue API routes — GET /api/venues."""

from __future__ import annotations

from typing import AsyncGenerator

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.common import ApiResponse, PaginatedResponse

router = APIRouter(prefix="/api/venues", tags=["venues"])


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


@router.get("", summary="List all venues")
async def list_venues(
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=50, ge=1, le=100, description="Items per page"),
    session: AsyncSession = Depends(_get_db),
) -> ApiResponse[PaginatedResponse]:
    """Return a paginated list of venues with timezone information."""
    from app.services.venue_service import VenueService

    svc = VenueService(session)
    items, total = await svc.get_all_venues(page=page, page_size=page_size)
    paginated = PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )
    return ApiResponse(data=paginated)
