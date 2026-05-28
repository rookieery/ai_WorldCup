"""AI chat request, SSE event, and team analysis VO schemas."""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


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
