"""Group standing and group detail VO schemas."""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field

from app.schemas.match_schema import MatchResponse
from app.schemas.team_schema import TeamListResponse


class GroupStandingResponse(BaseModel):
    """VO for one team's row inside a group standings table."""

    id: int
    team: TeamListResponse
    group_label: str
    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    goals_for: int = 0
    goals_against: int = 0
    goal_difference: int = 0
    points: int = 0
    position: int = 0

    model_config = {"from_attributes": True}


class GroupDetailResponse(BaseModel):
    """VO for a single group's complete detail — standings + matches."""

    group_label: str
    standings: List[GroupStandingResponse] = Field(default_factory=list)
    matches: List[MatchResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}
