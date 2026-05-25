"""Pydantic models for scraped data validation.

These models define the expected shape of data returned by web scrapers.
Every scraped response is validated against these schemas before being
passed to services for persistence.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ── Scraped match schedule ──────────────────────────────────────────────


class ScrapedMatch(BaseModel):
    """A single match extracted from the FIFA schedule page."""

    external_id: str = Field(..., description="FIFA match identifier")
    home_team: str = Field(..., description="Home team name or code")
    away_team: str = Field(..., description="Away team name or code")
    kickoff_utc: datetime = Field(..., description="Kickoff time in UTC")
    stage: str = Field(..., description="Tournament stage (group / R32 / R16 / ...)")
    group_label: Optional[str] = Field(
        default=None, description="Group letter (A-L) for group stage matches"
    )
    venue_name: Optional[str] = Field(
        default=None, description="Stadium / venue name"
    )
    status: str = Field(default="upcoming", description="Match status")
    home_score: Optional[int] = Field(default=None, description="Home team score")
    away_score: Optional[int] = Field(default=None, description="Away team score")

    @field_validator("stage")
    @classmethod
    def validate_stage(cls, v: str) -> str:
        allowed = {"group", "R32", "R16", "QF", "SF", "3rd", "F"}
        if v not in allowed:
            raise ValueError(f"Invalid stage: {v!r}. Must be one of {allowed}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"upcoming", "live", "finished", "postponed"}
        if v not in allowed:
            raise ValueError(f"Invalid status: {v!r}. Must be one of {allowed}")
        return v

    model_config = {"from_attributes": True}


class ScrapedSchedule(BaseModel):
    """A batch of scraped matches from the schedule page."""

    matches: List[ScrapedMatch] = Field(default_factory=list)
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    source_url: str = Field(..., description="URL the data was scraped from")


# ── Scraped live score ──────────────────────────────────────────────────


class ScrapedLiveEvent(BaseModel):
    """A single event scraped from a live match feed."""

    event_type: str = Field(..., description="Event type (goal / yellow_card / ...)")
    minute: int = Field(..., ge=0, description="Minute the event occurred")
    team_side: str = Field(..., description="home or away")
    player_name: Optional[str] = Field(default=None, description="Player name")

    @field_validator("team_side")
    @classmethod
    def validate_team_side(cls, v: str) -> str:
        if v not in ("home", "away"):
            raise ValueError(f"team_side must be 'home' or 'away', got {v!r}")
        return v


class ScrapedLiveScore(BaseModel):
    """Real-time score data for a single match currently in progress."""

    match_id: str = Field(..., description="External match identifier")
    home_score: int = Field(..., ge=0, description="Home team current score")
    away_score: int = Field(..., ge=0, description="Away team current score")
    status: str = Field(default="live", description="Match status")
    activity_level: int = Field(
        default=0, ge=0, le=100, description="Match activity level (0-100)"
    )
    events: List[ScrapedLiveEvent] = Field(
        default_factory=list, description="Recent match events"
    )

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"upcoming", "live", "finished", "postponed"}
        if v not in allowed:
            raise ValueError(f"Invalid status: {v!r}. Must be one of {allowed}")
        return v

    model_config = {"from_attributes": True}


class ScrapedLiveScoreBatch(BaseModel):
    """A batch of live scores scraped from the live scores page."""

    matches: List[ScrapedLiveScore] = Field(default_factory=list)
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    source_url: str = Field(..., description="URL the data was scraped from")


# ── Scraped match result ────────────────────────────────────────────────


class ScrapedEvent(BaseModel):
    """A single event (goal, card, substitution) scraped from a match page."""

    event_type: str = Field(..., description="Event type (goal / yellow_card / ...)")
    minute: int = Field(..., ge=0, description="Minute the event occurred")
    team_side: str = Field(..., description="home or away")
    player_name: Optional[str] = Field(default=None, description="Player name")

    @field_validator("team_side")
    @classmethod
    def validate_team_side(cls, v: str) -> str:
        if v not in ("home", "away"):
            raise ValueError(f"team_side must be 'home' or 'away', got {v!r}")
        return v


class ScrapedMatchResult(BaseModel):
    """Detailed result for a single match scraped from the match page."""

    external_id: str = Field(..., description="FIFA match identifier")
    status: str = Field(default="finished", description="Match status")
    home_score: int = Field(..., ge=0, description="Home team final score")
    away_score: int = Field(..., ge=0, description="Away team final score")
    events: List[ScrapedEvent] = Field(default_factory=list)
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    source_url: str = Field(..., description="URL the data was scraped from")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"upcoming", "live", "finished", "postponed"}
        if v not in allowed:
            raise ValueError(f"Invalid status: {v!r}. Must be one of {allowed}")
        return v

    model_config = {"from_attributes": True}