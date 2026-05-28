"""Bracket (knockout tree) VO schemas."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class BracketTeamResponse(BaseModel):
    """VO for a team slot inside a bracket match.

    When the team is still TBD, ``code`` is ``None`` and qualifying context
    (``from_group`` / ``from_position``) is provided instead.
    """

    id: Optional[int] = None
    name: Optional[str] = None
    name_zh: Optional[str] = None
    code: Optional[str] = None
    flag: Optional[str] = None
    score: Optional[int] = None

    # Context for TBD teams
    from_group: Optional[str] = Field(
        default=None, description="Group label when team is TBD (e.g. 'A')"
    )
    from_position: Optional[int] = Field(
        default=None, description="Group rank when team is TBD (e.g. 1 for 1st place)"
    )

    model_config = {"from_attributes": True}


class BracketMatchResponse(BaseModel):
    """VO for a single match inside the bracket tree."""

    id: int
    external_id: str
    stage: str
    home_team: BracketTeamResponse
    away_team: BracketTeamResponse
    status: str = "upcoming"
    kickoff_utc: Optional[str] = None
    position: Optional[int] = None

    model_config = {"from_attributes": True}


class BracketRoundResponse(BaseModel):
    """VO for one round of the bracket (e.g. all R16 matches)."""

    round_name: str = Field(description="Round identifier (R32 / R16 / QF / SF / 3rd / F)")
    display_name: str = Field(description="Human-readable round name")
    matches: List[BracketMatchResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class BracketTreeResponse(BaseModel):
    """Top-level VO for the entire knockout bracket tree."""

    rounds: List[BracketRoundResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}
