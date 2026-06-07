"""Pydantic DTOs for Feishu (Lark) Bot integration.

Covers inbound webhook events, intent parsing results, and card config.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Intent types ─────────────────────────────────────────────────────────────


class FeishuIntent(str, Enum):
    """Supported user intents parsed from Feishu messages."""

    TODAY_MATCHES = "today_matches"
    MATCH_QUERY = "match_query"
    MATCH_ANALYSIS = "match_analysis"
    CHAMPION_PREDICT = "champion_predict"
    GENERAL_CHAT = "general_chat"


class FeishuIntentResult(BaseModel):
    """Structured result of intent parsing from a user message."""

    intent: FeishuIntent = FeishuIntent.GENERAL_CHAT
    team1: Optional[str] = None
    team2: Optional[str] = None
    team_name: Optional[str] = None
    raw_text: str = ""
    custom_strategy: bool = False


# ── Webhook event payloads ──────────────────────────────────────────────────


class FeishuEventHeader(BaseModel):
    """Header of a Feishu event callback."""

    event_id: str = ""
    event_type: str = ""
    create_time: str = ""
    token: str = ""
    app_id: str = ""
    tenant_key: str = ""


class FeishuMessageContent(BaseModel):
    """Text content extracted from a Feishu message event."""

    text: str = ""


class FeishuSender(BaseModel):
    """Sender information from a Feishu message event."""

    sender_id: Dict[str, str] = Field(default_factory=dict)
    sender_type: str = ""
    tenant_key: str = ""


class FeishuMessageEvent(BaseModel):
    """Inner ``message`` object within the ``event`` payload."""

    message_id: str = ""
    root_id: str = ""
    parent_id: str = ""
    create_time: str = ""
    update_time: str = ""
    chat_id: str = ""
    chat_type: str = ""
    message_type: str = ""
    content: str = ""
    mentions: List[Dict[str, Any]] = Field(default_factory=list)


class FeishuEventPayload(BaseModel):
    """Inner ``event`` payload of ``im.message.receive_v1``.

    Standard Feishu webhook format nests ``sender`` and ``message``
    as separate children under ``event``.
    """

    sender: FeishuSender = Field(default_factory=FeishuSender)
    message: FeishuMessageEvent = Field(default_factory=FeishuMessageEvent)


class FeishuWebhookEvent(BaseModel):
    """Top-level Feishu event callback body."""

    schema_: str = Field("", alias="schema")
    header: FeishuEventHeader = Field(default_factory=FeishuEventHeader)
    event: Optional[FeishuEventPayload] = None


# ── Card config ─────────────────────────────────────────────────────────────


class FeishuCardConfig(BaseModel):
    """Configuration for Feishu interactive card rendering."""

    wide_screen_mode: bool = True
    enable_forward: bool = True
