"""Stats schema — request/response models for the stats endpoints."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ScorerItem(BaseModel):
    """A single row in the scorer leaderboard."""

    rank: int = Field(description="Leaderboard position (1-based)")
    player_name: str = Field(description="Player name")
    team_code: str = Field(description="3-letter team code, e.g. BRA")
    team_name: str = Field(description="Team name in English")
    team_name_zh: str = Field(description="Team name in Chinese")
    team_flag: str = Field(description="Team flag emoji")
    goals: int = Field(description="Total goals scored")
    assists: int = Field(default=0, description="Total assists")

    model_config = {"from_attributes": True}
