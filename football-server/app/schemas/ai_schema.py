"""AI chat request, SSE event, team analysis VO, and match analysis schemas."""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class ChatMessageItem(BaseModel):
    """A single message in the chat history sent by the client."""

    role: Literal["user", "assistant"] = Field(
        ..., description="Who authored the message"
    )
    content: str = Field(..., min_length=1, description="Message text")


class ChatContext(BaseModel):
    """Client-side context that accompanies a chat request."""

    current_view: Optional[str] = Field(
        default=None, description="Current UI view (timeline / bracket / group)"
    )
    selected_date: Optional[str] = Field(
        default=None, description="Selected date on the timeline (YYYY-MM-DD)"
    )
    timezone: Optional[str] = Field(
        default=None, description="User's IANA timezone identifier"
    )


class ChatRequest(BaseModel):
    """DTO for initiating an AI chat stream."""

    messages: List[ChatMessageItem] = Field(
        ..., min_length=1, description="Chat history (last message is the current question)"
    )
    context: Optional[ChatContext] = Field(
        default=None, description="Optional client-side context for personalised responses"
    )
    lang: Literal["zh-CN", "en-US"] = Field(
        default="zh-CN", description="Language preference for AI responses"
    )


class SSEEvent(BaseModel):
    """A single Server-Sent Event in the AI chat stream."""

    type: Literal["thinking", "answer", "analysis", "done", "error"] = Field(
        ..., description="Event type discriminator"
    )
    content: Optional[str] = Field(
        default=None, description="Text delta for thinking / answer / error events"
    )
    data: Optional[dict] = Field(
        default=None, description="Structured payload for analysis events"
    )

    model_config = {"from_attributes": True}


class TeamAnalysisResponse(BaseModel):
    """VO for AI-generated team analysis with structured dimensions."""

    team_code: str = Field(..., description="Team code being analysed")
    team_name: str = Field(..., description="Team English name")
    team_name_zh: str = Field(..., description="Team Chinese name")
    radar: List[dict] = Field(
        default_factory=list,
        description="5-dimension radar data [{dimension, value, label}]",
    )
    win_probability: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Win probability (0-1)"
    )
    insights: List[str] = Field(
        default_factory=list, description="Key insight bullet points"
    )

    model_config = {"from_attributes": True}


# ── Match Analysis request / response schemas ────────────────────────────

_VALID_STAGES = {"group", "R32", "R16", "QF", "SF", "3rd", "F"}
_VALID_STATUSES = {"upcoming", "live", "finished"}
_VALID_LANGS = {"zh-CN", "en-US"}


class TeamBrief(BaseModel):
    """Brief team information for match analysis requests."""

    name: str = Field(..., description="Team English name")
    name_zh: str = Field(..., description="Team Chinese name")
    code: str = Field(..., min_length=2, max_length=3, description="FIFA team code")
    flag: str = Field(..., description="Team flag emoji or URL")


class MatchEventBrief(BaseModel):
    """Brief match event for analysis context."""

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


class MatchAnalysisRequest(BaseModel):
    """Request body for the AI match analysis streaming endpoint."""

    match_id: int = Field(..., description="Match primary key")
    stage: str = Field(..., description="Tournament stage")
    skill_id: Optional[str] = Field(
        default=None,
        description="Skill to use; omit to auto-detect from stage",
    )
    home_team: TeamBrief = Field(..., description="Home team brief info")
    away_team: TeamBrief = Field(..., description="Away team brief info")
    home_score: Optional[int] = Field(default=None, description="Home team score")
    away_score: Optional[int] = Field(default=None, description="Away team score")
    status: str = Field(..., description="Match status")
    group_label: Optional[str] = Field(
        default=None, description="Group letter (A-L), only for group stage"
    )
    round: Optional[str] = Field(default=None, description="Round description")
    match_day: Optional[int] = Field(default=None, description="Match day number")
    events: Optional[List[MatchEventBrief]] = Field(
        default=None, description="Match events timeline"
    )
    lang: str = Field(..., description="Response language")

    @field_validator("stage")
    @classmethod
    def validate_stage(cls, v: str) -> str:
        if v not in _VALID_STAGES:
            raise ValueError(
                f"Invalid stage: {v!r}. Must be one of {_VALID_STAGES}"
            )
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in _VALID_STATUSES:
            raise ValueError(
                f"Invalid status: {v!r}. Must be one of {_VALID_STATUSES}"
            )
        return v

    @field_validator("lang")
    @classmethod
    def validate_lang(cls, v: str) -> str:
        if v not in _VALID_LANGS:
            raise ValueError(
                f"Invalid lang: {v!r}. Must be one of {_VALID_LANGS}"
            )
        return v


class ChampionshipAnalysisRequest(BaseModel):
    """Request body for the championship/runner-up prediction streaming endpoint."""

    skill_id: Optional[str] = Field(
        default=None,
        description="Skill to use; defaults to championship_predict",
    )
    simulation_count: int = Field(
        default=2000,
        ge=100,
        le=10000,
        description="Number of Monte Carlo simulation runs (100-10000)",
    )
    lang: str = Field(
        default="zh-CN",
        description="Response language",
    )

    @field_validator("lang")
    @classmethod
    def validate_lang(cls, v: str) -> str:
        if v not in _VALID_LANGS:
            raise ValueError(
                f"Invalid lang: {v!r}. Must be one of {_VALID_LANGS}"
            )
        return v


class SkillInfo(BaseModel):
    """Metadata for an AI analysis Skill."""

    skill_id: str = Field(..., description="Unique skill identifier")
    name: str = Field(..., description="Skill English name")
    name_zh: str = Field(..., description="Skill Chinese name")
    description: str = Field(..., description="Skill English description")
    description_zh: str = Field(..., description="Skill Chinese description")
    applicable_stages: List[str] = Field(
        ..., description="Tournament stages this skill applies to"
    )
