"""Bracket API routes — GET /api/bracket, GET /api/bracket/predictions."""

from __future__ import annotations

from typing import AsyncGenerator

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.common import ApiResponse

router = APIRouter(prefix="/api/bracket", tags=["bracket"])


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


@router.get("", summary="Full knockout bracket tree")
async def get_full_bracket(
    timezone: str | None = Query(
        default=None, description="Target IANA timezone for kickoff conversion"
    ),
    lang: str = Query(default="en", description="Language: en or zh"),
    session: AsyncSession = Depends(_get_db),
) -> ApiResponse:
    """Return the complete knockout bracket (R32 -> R16 -> QF -> SF -> 3rd -> F).

    Data is grouped by round, each round sorted by position.
    Teams that are still TBD include fromGroup / fromPosition context.
    """
    from app.services.bracket_service import BracketService

    svc = BracketService(session)
    tree = await svc.get_full_bracket(lang=lang, timezone_name=timezone)
    return ApiResponse(data=tree)


@router.get("/predictions", summary="AI bracket predictions")
async def get_bracket_predictions(
    session: AsyncSession = Depends(_get_db),
) -> ApiResponse:
    """Return AI-predicted knockout bracket path.

    Phase 3 will integrate with the AI service.
    Currently returns TBD status.
    """
    from app.services.bracket_service import BracketService

    svc = BracketService(session)
    predictions = await svc.get_predictions()
    return ApiResponse(data=predictions)
