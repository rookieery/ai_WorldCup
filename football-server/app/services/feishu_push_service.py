"""Feishu push notification service.

Subscribes to match events (kickoff, goal, final result) broadcast by
``LiveService._broadcast_event`` and forwards them as Feishu interactive
card messages to a configured group chat.

Module-level ``get_push_service()`` singleton mirrors the
``ConnectionManager.get_manager()`` pattern.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from redis.asyncio import Redis

from app.config import settings
from app.schemas.ws_schema import WSEventType
from app.services.feishu_card_builder import (
    build_match_end_card,
    build_score_update_card,
    build_match_start_card,
)
from app.services.feishu_client import FeishuClient

logger = logging.getLogger(__name__)

# ── Event types that trigger a push ─────────────────────────────────────────

_PUSH_EVENTS: set[WSEventType] = {
    WSEventType.MATCH_START,
    WSEventType.SCORE_UPDATE,
    WSEventType.MATCH_END,
}

# ── Debounce intervals (seconds) per event type ────────────────────────────

_DEBOUNCE_SECONDS: Dict[WSEventType, float] = {
    WSEventType.MATCH_START: 60.0,
    WSEventType.SCORE_UPDATE: 10.0,
    WSEventType.MATCH_END: 60.0,
}


class FeishuPushService:
    """Push match event notifications to a Feishu group chat.

    Hooks into the live event broadcast pipeline and forwards match events
    as Feishu cards.  Fire-and-forget: errors are logged but never propagate
    upstream to ``LiveService``.
    """

    def __init__(
        self,
        feishu_client: FeishuClient,
        match_service: Any,
        redis: Optional[Redis] = None,
    ) -> None:
        self._client = feishu_client
        self._match_service = match_service
        self._redis = redis
        self._chat_id: str = settings.FEISHU_CHAT_ID
        # Debounce tracking: {(match_id, event_type): last_push_timestamp}
        self._last_push: Dict[tuple[int, str], float] = {}

    # ── Public API ───────────────────────────────────────────────────────

    async def handle_event(
        self,
        event_type: WSEventType,
        data: Dict[str, Any],
    ) -> None:
        """Route a broadcast event to the appropriate card push.

        Should be called from ``_broadcast_event`` alongside the existing
        WebSocket broadcast.  Failures are logged silently.
        """
        if event_type not in _PUSH_EVENTS:
            return

        match_id: int = data.get("match_id", 0)
        if match_id <= 0:
            return

        # Debounce check
        key = (match_id, event_type.value)
        now = time.monotonic()
        cooldown = _DEBOUNCE_SECONDS.get(event_type, 10.0)
        last = self._last_push.get(key, 0.0)
        if now - last < cooldown:
            logger.debug(
                "Feishu push debounced for match %d %s (%.1fs remaining)",
                match_id,
                event_type.value,
                cooldown - (now - last),
            )
            return
        self._last_push[key] = now

        try:
            if event_type == WSEventType.MATCH_START:
                await self._push_match_start(match_id)
            elif event_type == WSEventType.SCORE_UPDATE:
                await self._push_score_update(
                    match_id,
                    data.get("home_score", 0),
                    data.get("away_score", 0),
                )
            elif event_type == WSEventType.MATCH_END:
                await self._push_match_end(
                    match_id,
                    data.get("home_score", 0),
                    data.get("away_score", 0),
                )
        except Exception:
            logger.warning(
                "Feishu push failed for match %d %s",
                match_id,
                event_type.value,
                exc_info=True,
            )

    # ── Push handlers ────────────────────────────────────────────────────

    async def _enrich_match(self, match_id: int) -> Optional[Dict[str, Any]]:
        """Fetch full match details from ``MatchService``.

        Returns ``None`` if the match cannot be found (logged as warning).
        """
        try:
            return await self._match_service.get_match_by_id(
                match_id, lang="zh"
            )
        except Exception:
            logger.warning("Cannot enrich match %d for Feishu push", match_id, exc_info=True)
            return None

    async def _push_match_start(self, match_id: int) -> None:
        """Fetch match details, build card, send to Feishu chat."""
        match_data = await self._enrich_match(match_id)
        if match_data is None:
            return

        card = build_match_start_card(match_data)
        await self._client.send_card_message(
            self._chat_id, card, redis=self._redis
        )
        logger.info("Feishu push: MATCH_START for match %d", match_id)

    async def _push_score_update(
        self,
        match_id: int,
        home_score: int,
        away_score: int,
    ) -> None:
        """Fetch match details, build score card, send."""
        match_data = await self._enrich_match(match_id)
        if match_data is None:
            return

        card = build_score_update_card(
            match_data, home_score=home_score, away_score=away_score
        )
        await self._client.send_card_message(
            self._chat_id, card, redis=self._redis
        )
        logger.info("Feishu push: SCORE_UPDATE for match %d", match_id)

    async def _push_match_end(
        self,
        match_id: int,
        home_score: int,
        away_score: int,
    ) -> None:
        """Fetch match details, build result card, send."""
        match_data = await self._enrich_match(match_id)
        if match_data is None:
            return

        card = build_match_end_card(
            match_data, home_score=home_score, away_score=away_score
        )
        await self._client.send_card_message(
            self._chat_id, card, redis=self._redis
        )
        logger.info("Feishu push: MATCH_END for match %d", match_id)


# ── Module-level singleton ──────────────────────────────────────────────────

_push_service: Optional[FeishuPushService] = None


def init_push_service(
    feishu_client: FeishuClient,
    match_service: Any,
    redis: Optional[Redis] = None,
) -> FeishuPushService:
    """Create and store the global ``FeishuPushService`` singleton."""
    global _push_service  # noqa: PLW0603
    _push_service = FeishuPushService(feishu_client, match_service, redis=redis)
    logger.info("Feishu push service initialized (chat_id=%s)", settings.FEISHU_CHAT_ID)
    return _push_service


def get_push_service() -> Optional[FeishuPushService]:
    """Return the global push service, or ``None`` if not initialized."""
    return _push_service
