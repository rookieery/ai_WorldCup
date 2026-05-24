"""Team-related DTO (request) and VO (response) schemas."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


# ── Request DTOs ─────────────────────────────────────────────────────────────

class TeamCreate(BaseModel):
    """DTO for creating a new team."""

    name: str = Field(..., min_length=1, max_length=100, description="English team name")
    name_zh: str = Field(..., min_length=1, max_length=100, description="Chinese team name")
    code: str = Field(..., min_length=3, max_length=3, description="3-letter team code")
    flag: str = Field(default="", max_length=20, description="Flag emoji")
    fifa_ranking: int = Field(default=0, ge=0, description="Current FIFA ranking")
    group_label: str = Field(..., min_length=1, max_length=1, description="Group letter A-L")
    confederation: str = Field(default="", max_length=20, description="Confederation code")
    world_cup_appearances: int = Field(
        default=0, ge=0, description="Number of World Cup appearances"
    )


class TeamUpdate(BaseModel):
    """DTO for partially updating an existing team.

    All fields are optional; only provided fields will be updated.
    """

    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    name_zh: Optional[str] = Field(default=None, min_length=1, max_length=100)
    flag: Optional[str] = Field(default=None, max_length=20)
    fifa_ranking: Optional[int] = Field(default=None, ge=0)
    confederation: Optional[str] = Field(default=None, max_length=20)
    world_cup_appearances: Optional[int] = Field(default=None, ge=0)


# ── Response VOs ─────────────────────────────────────────────────────────────

class TeamResponse(BaseModel):
    """VO returned when reading a single team."""

    id: int
    name: str
    name_zh: str
    code: str
    flag: str
    fifa_ranking: int
    group_label: str
    confederation: str
    world_cup_appearances: int

    model_config = {"from_attributes": True}


class TeamListResponse(BaseModel):
    """Minimal VO used in list / dropdown contexts.

    Intentionally omits less frequently needed fields to keep payloads small.
    """

    id: int
    name: str
    name_zh: str
    code: str
    flag: str
    group_label: str

    model_config = {"from_attributes": True}
