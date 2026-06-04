"""Feishu Bot webhook controller.

Handles:
- URL verification challenge (during bot setup on open.feishu.cn)
- Event callback verification via ``FEISHU_VERIFY_TOKEN``
- Inbound ``im.message.receive_v1`` events dispatched to ``FeishuBotService``

Phase 3 interactive bot endpoint.  Phase 1 push notifications do not
require this controller — they are driven by ``FeishuPushService`` via
the ``LiveService._broadcast_event`` hook.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.config import settings
from app.schemas.common import ApiResponse
from app.schemas.feishu_schema import FeishuWebhookEvent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/feishu", tags=["feishu"])


@router.post(
    "/webhook",
    summary="Feishu event callback endpoint",
)
async def feishu_webhook(
    request: Request,
) -> JSONResponse:
    """Receive and dispatch Feishu event callbacks.

    1. **URL verification** — During bot setup Feishu sends a challenge
       request.  We echo the ``challenge`` value back.
    2. **Event verification** — Check ``header.token`` against
       ``FEISHU_VERIFY_TOKEN``.
    3. **Message dispatch** — Hand off to ``FeishuBotService`` for
       intent parsing and AI response (fire-and-forget ``asyncio.Task``).

    Always returns HTTP 200 immediately to avoid Feishu webhook timeout.
    """
    try:
        body: Dict[str, Any] = await request.json()
    except Exception:
        logger.warning("Feishu webhook: invalid JSON body")
        return JSONResponse({"code": -1, "msg": "invalid json"}, status_code=400)

    # ── 1. URL verification challenge ───────────────────────────────────
    challenge = body.get("challenge")
    if challenge and body.get("type") == "url_verification":
        token = body.get("token", "")
        if settings.FEISHU_VERIFY_TOKEN and token != settings.FEISHU_VERIFY_TOKEN:
            logger.warning("Feishu challenge token mismatch")
            return JSONResponse({"code": -1, "msg": "token mismatch"}, status_code=403)
        return JSONResponse({"challenge": challenge})

    # ── 2. Parse event ──────────────────────────────────────────────────
    try:
        event = FeishuWebhookEvent.model_validate(body)
        logger.info(
            "Feishu webhook: event_type=%s, event=%s",
            event.header.event_type,
            "present" if event.event else "None",
        )
    except Exception:
        logger.warning("Feishu webhook: cannot parse event body: %s", body[:200])
        return JSONResponse({"code": 0})

    # ── 3. Verify token ─────────────────────────────────────────────────
    if settings.FEISHU_VERIFY_TOKEN and event.header.token != settings.FEISHU_VERIFY_TOKEN:
        logger.warning("Feishu event token mismatch (event_id=%s)", event.header.event_id)
        return JSONResponse({"code": 0})

    # ── 4. Dispatch message event (Phase 3) ─────────────────────────────
    if (
        settings.FEISHU_BOT_ENABLED
        and event.header.event_type == "im.message.receive_v1"
        and event.event is not None
    ):
        asyncio.create_task(_dispatch_bot_message(event))
    else:
        logger.debug(
            "Feishu event ignored (type=%s, bot_enabled=%s)",
            event.header.event_type,
            settings.FEISHU_BOT_ENABLED,
        )

    # Always return 200 immediately
    return JSONResponse({"code": 0})


async def _dispatch_bot_message(event: FeishuWebhookEvent) -> None:
    """Fire-and-forget: hand the event to ``FeishuBotService``."""
    try:
        from app.dependencies import get_shared_feishu_client, _session_factory
        from app.services.feishu_bot_service import FeishuBotService
        from app.services.ai_service import AIService
        from app.redis.client import get_redis

        # ── Resolve FeishuClient (reuse shared singleton) ──────────────
        feishu_client = get_shared_feishu_client()

        # ── Resolve MatchService (requires DB session + optional Redis) ─
        match_service = None
        if _session_factory is not None:
            try:
                from app.services.match_service import MatchService
                redis = get_redis()
                async with _session_factory() as session:
                    match_service = MatchService(session, redis=redis)
                    bot_svc = FeishuBotService(
                        feishu_client=feishu_client,
                        ai_service=AIService(),
                        match_service=match_service,
                    )
                    await bot_svc.handle_message(event)
                return  # early return — session cleaned up via async with
            except Exception:
                logger.warning("Failed to create MatchService for Feishu bot", exc_info=True)

        # Fallback: no match_service available (bot still works for AI chat)
        bot_svc = FeishuBotService(
            feishu_client=feishu_client,
            ai_service=AIService(),
        )
        await bot_svc.handle_message(event)
    except Exception:
        logger.warning("Feishu bot dispatch failed", exc_info=True)


@router.get(
    "/health",
    summary="Feishu integration health check",
    response_model=ApiResponse[Dict[str, Any]],
)
async def feishu_health() -> ApiResponse[Dict[str, Any]]:
    """Return Feishu integration configuration status."""
    return ApiResponse(
        data={
            "enabled": settings.FEISHU_ENABLED,
            "push_enabled": settings.FEISHU_PUSH_ENABLED,
            "bot_enabled": settings.FEISHU_BOT_ENABLED,
            "configured": settings.feishu_configured,
            "chat_id_set": bool(settings.FEISHU_CHAT_ID),
        },
    )
