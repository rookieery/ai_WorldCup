"""Group API routes — GET /api/groups, GET /api/groups/:group."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_group_service
from app.schemas.common import ApiResponse
from app.services.group_service import GroupService

router = APIRouter(prefix="/api/groups", tags=["groups"])


# ── routes ──────────────────────────────────────────────────────────────────


@router.get("", summary="List all 12 groups with standings")
async def list_groups(
    lang: str = Query(default="en", description="Language: en or zh"),
    svc: GroupService = Depends(get_group_service),
) -> ApiResponse:
    """Return standings overview for all 12 groups (A-L).

    Each group contains its standings sorted by points desc,
    goal_difference desc, goals_for desc.
    """
    groups = await svc.get_all_groups(lang=lang)
    return ApiResponse(data=groups)


@router.get("/{group}", summary="Get single group detail (A-L)")
async def get_group_detail(
    group: str,
    timezone: str | None = Query(
        default=None, description="Target IANA timezone for local_time conversion"
    ),
    lang: str = Query(default="en", description="Language: en or zh"),
    svc: GroupService = Depends(get_group_service),
) -> ApiResponse:
    """Return standings + matches for a single group.

    ``group`` must be a single letter from A to L.
    """
    detail = await svc.get_group_detail(
        group,
        timezone_name=timezone,
        lang=lang,
    )
    return ApiResponse(data=detail)
