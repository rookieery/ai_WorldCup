"""Cheer (fan voting) API routes — GET /api/cheers/:matchId, POST /api/cheers/:matchId."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.redis.client import get_redis
from app.schemas.cheer_schema import CheerResponse, CheerVoteRequest
from app.schemas.common import ApiResponse
from app.services.cheer_service import CheerService

router = APIRouter(prefix="/api/cheers", tags=["cheers"])


# ── dependency helpers ────────────────────────────────────────────────────────


def _get_client_ip(request: Request) -> str:
    """Extract the client IP from the request, respecting ``X-Forwarded-For``."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _get_cheer_service() -> CheerService:
    """Create a ``CheerService`` with an optional Redis client."""
    return CheerService(redis=get_redis())


# ── routes ────────────────────────────────────────────────────────────────────


@router.get(
    "/{match_id}",
    summary="Get cheer counts for a match",
    response_model=ApiResponse[CheerResponse],
)
async def get_cheers(
    match_id: int,
    svc: CheerService = Depends(_get_cheer_service),
) -> ApiResponse[CheerResponse]:
    """Return the current home/away cheer counts for the given match."""
    result = await svc.get_cheers(match_id)
    return ApiResponse(data=result)


@router.post(
    "/{match_id}",
    summary="Submit a cheer vote",
    response_model=ApiResponse[CheerResponse],
)
async def vote_cheer(
    match_id: int,
    body: CheerVoteRequest,
    request: Request,
    svc: CheerService = Depends(_get_cheer_service),
) -> ApiResponse[CheerResponse]:
    """Submit a cheer vote for the home or away team.

    A single IP may vote at most once per match within the cooldown window.
    """
    client_ip = _get_client_ip(request)
    result = await svc.vote_cheer(match_id, body.side, client_ip)
    return ApiResponse(data=result)
