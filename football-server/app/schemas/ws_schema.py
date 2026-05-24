"""WebSocket event type enum and message VO schema."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict

from pydantic import BaseModel, Field


class WSEventType(str, Enum):
    """Discriminator for WebSocket broadcast events."""

    SCORE_UPDATE = "score_update"
    MATCH_START = "match_start"
    MATCH_END = "match_end"
    ACTIVITY_UPDATE = "activity_update"
    CHEER_UPDATE = "cheer_update"
    BRACKET_UPDATE = "bracket_update"


class WSMessage(BaseModel):
    """Envelope for all WebSocket messages exchanged between server and clients."""

    event: WSEventType = Field(..., description="Event type discriminator")
    payload: Dict[str, Any] = Field(
        default_factory=dict, description="Event-specific data payload"
    )

    model_config = {"from_attributes": True}
