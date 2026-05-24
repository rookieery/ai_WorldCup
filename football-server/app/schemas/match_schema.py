"""Match and MatchEvent DTO / VO schemas."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.team_schema import TeamListResponse
from app.schemas.venue_schema import VenueResponse


# ── Request DTOs ─────────────────────────────────────────────────────────────

class MatchQueryParams(BaseModel):
    """Query-parameter DTO for filtering the match list endpoint."""

    date: Optional[str] = Field(
        default=None, description="Filter by kickoff date (YYYY-MM-DD, UTC)"
    )
    stage: Optional[str] = Field(
        default=None, description="Filter by stage (group / R32 / R16 / QF / SF / 3rd / F)"
    )
    group: Optional[str] = Field(
        default=None, max_length=1, description="Filter by group letter (A-L)"
    )
    team: Optional[str] = Field(
        default=None, max_length=3, description="Filter by team code"
    )
    status: Optional[str] = Field(
        default=None, description="Filter by status (upcoming / live / finished / postponed)"
    )


# ── Response VOs ─────────────────────────────────────────────────────────────

class MatchEventResponse(BaseModel):
    """VO for a single match event (goal, card, substitution, etc.)."""

    id: int
    match_id: int
    event_type: str
    minute: int
    team_side: str
    player_name: Optional[str] = None

    model_config = {"from_attributes": True}


class MatchResponse(BaseModel):
    """VO for a match in list / overview contexts.

    Includes nested team and venue information for one-stop rendering.
    """

    id: int
    external_id: str
    home_team: TeamListResponse
    away_team: TeamListResponse
    venue: VenueResponse
    stage: str
    group_label: Optional[str] = None
    round: str = ""
    match_day: Optional[int] = None
    kickoff_utc: datetime
    local_time: Optional[str] = Field(
        default=None, description="Kickoff in user's requested timezone (HH:MM)"
    )
    host_time: Optional[str] = Field(
        default=None, description="Kickoff in venue's local timezone (HH:MM)"
    )
    status: str
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    is_big_match: bool = False
    activity_level: int = 0

    model_config = {"from_attributes": True}


class MatchDetailResponse(MatchResponse):
    """Extended match VO that additionally includes match events."""

    events: List[MatchEventResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}
