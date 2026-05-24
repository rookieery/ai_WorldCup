"""Cheer (fan voting) DTO and VO schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class CheerVoteRequest(BaseModel):
    """DTO for submitting a cheer vote."""

    side: Literal["home", "away"] = Field(
        ..., description="Which side to vote for: 'home' or 'away'"
    )


class CheerResponse(BaseModel):
    """VO returned when reading cheer counts for a match."""

    match_id: int
    home: int = Field(default=0, ge=0, description="Total cheers for the home team")
    away: int = Field(default=0, ge=0, description="Total cheers for the away team")

    model_config = {"from_attributes": True}
