"""Bracket API routes — GET /api/bracket, GET /api/bracket/predictions."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_bracket_service
from app.schemas.common import ApiResponse
from app.services.bracket_service import BracketService

router = APIRouter(prefix="/api/bracket", tags=["bracket"])


# ── routes ──────────────────────────────────────────────────────────────────


@router.get("", summary="Full knockout bracket tree")
async def get_full_bracket(
    timezone: str | None = Query(
        default=None, description="Target IANA timezone for kickoff conversion"
    ),
    lang: str = Query(default="en", description="Language: en or zh"),
    svc: BracketService = Depends(get_bracket_service),
) -> ApiResponse:
    """Return the complete knockout bracket (R32 -> R16 -> QF -> SF -> 3rd -> F).

    Data is grouped by round, each round sorted by position.
    Teams that are still TBD include fromGroup / fromPosition context.
    """
    tree = await svc.get_full_bracket(lang=lang, timezone_name=timezone)
    return ApiResponse(data=tree)


@router.get("/predictions", summary="AI bracket predictions")
async def get_bracket_predictions(
    svc: BracketService = Depends(get_bracket_service),
) -> ApiResponse:
    """Return AI-predicted knockout bracket path.

    Phase 3 will integrate with the AI service.
    Currently returns TBD status.
    """
    predictions = await svc.get_predictions()
    return ApiResponse(data=predictions)
