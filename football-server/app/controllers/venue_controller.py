"""Venue API routes — GET /api/venues."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_venue_service
from app.schemas.common import ApiResponse, PaginatedResponse
from app.services.venue_service import VenueService

router = APIRouter(prefix="/api/venues", tags=["venues"])


# ── routes ──────────────────────────────────────────────────────────────────


@router.get("", summary="List all venues")
async def list_venues(
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=50, ge=1, le=100, description="Items per page"),
    svc: VenueService = Depends(get_venue_service),
) -> ApiResponse[PaginatedResponse]:
    """Return a paginated list of venues with timezone information."""
    items, total = await svc.get_all_venues(page=page, page_size=page_size)
    paginated = PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )
    return ApiResponse(data=paginated)
