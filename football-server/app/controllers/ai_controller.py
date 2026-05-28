"""AI chat API routes — POST /api/ai/chat (SSE streaming endpoint).

Receives a ``ChatRequest`` body, builds the full prompt using
``PromptBuilder``, delegates to ``AIService.stream_chat()``, and returns
the result as a ``StreamingResponse`` with ``text/event-stream`` content type.
"""

from __future__ import annotations

import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, Depends

from app.dependencies import get_ai_service
from app.schemas.ai_schema import ChatRequest, SSEEvent
from app.services.ai_service import AIService
from app.services.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["ai"])


# ── SSE helpers ────────────────────────────────────────────────────────────


def _format_sse_event(event: SSEEvent) -> str:
    """Serialise an ``SSEEvent`` into a standard ``data: {json}\\n\\n`` line."""
    payload = event.model_dump(exclude_none=True)
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _format_done() -> str:
    """Return the terminal SSE sentinel."""
    return "data: [DONE]\n\n"


# ── streaming generator ────────────────────────────────────────────────────


async def _chat_stream(
    svc: AIService,
    body: ChatRequest,
) -> AsyncGenerator[str, None]:
    """Yield SSE-formatted strings for a single chat request.

    The pipeline is:
    1. Build system prompt via ``PromptBuilder``.
    2. Append user/assistant message history.
    3. Stream ``SSEEvent`` objects from ``AIService``.
    4. Convert each event to ``data: {json}\\n\\n``.
    5. Emit ``data: [DONE]\\n\\n`` on completion.
    """
    # Build the full message list: system prompt + context + chat history
    system_messages = PromptBuilder.build_system_prompt(lang=body.lang)
    context_messages = PromptBuilder.build_chat_context(body.messages)
    all_messages = system_messages + context_messages

    context_data = body.context.model_dump(exclude_none=True) if body.context else None

    try:
        async for event in svc.stream_chat(
            all_messages,
            context=context_data,
            lang=body.lang,
        ):
            yield _format_sse_event(event)
    except Exception:
        logger.exception("Unexpected error in AI chat stream")
        yield _format_sse_event(
            SSEEvent(
                type="error",
                content="An unexpected error occurred during streaming.",
            )
        )

    yield _format_done()


# ── routes ─────────────────────────────────────────────────────────────────


@router.post(
    "/chat",
    summary="AI chat (SSE streaming)",
)
async def chat(
    body: ChatRequest,
    svc: AIService = Depends(get_ai_service),
) -> "StreamingResponse":  # noqa: F821
    """Start an AI chat session and return the response as an SSE stream.

    The client should consume the stream by parsing ``data: {json}\\n\\n``
    lines until it receives ``data: [DONE]\\n\\n``.
    """
    from starlette.responses import StreamingResponse

    return StreamingResponse(
        _chat_stream(svc, body),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )