"""AI API routes — POST /api/ai/chat, POST /api/ai/match-analysis, GET /api/ai/skills.

Provides SSE streaming endpoints for AI chat and match analysis,
plus a static endpoint listing available analysis skills.
"""

from __future__ import annotations

import json
import logging
from typing import AsyncGenerator, List

from fastapi import APIRouter, Depends

from app.dependencies import get_ai_service
from app.schemas.ai_schema import (
    ChampionshipAnalysisRequest,
    ChatRequest,
    MatchAnalysisRequest,
    SkillInfo,
    SSEEvent,
)
from app.schemas.common import ApiResponse
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


async def _match_analysis_stream(
    svc: AIService,
    body: MatchAnalysisRequest,
) -> AsyncGenerator[str, None]:
    """Yield SSE-formatted strings for a skill-driven match analysis request.

    The pipeline is:
    1. Build the full prompt via ``PromptBuilder.build_skill_prompt``.
    2. Stream ``SSEEvent`` objects from ``AIService.stream_chat``.
    3. Convert each event to ``data: {json}\\n\\n``.
    4. Emit ``data: [DONE]\\n\\n`` on completion.

    Skill file loading failures are caught and surfaced as ``error`` events
    without breaking the stream, so the client always receives ``[DONE]``.
    """
    try:
        messages = PromptBuilder.build_skill_prompt(body)
    except Exception:
        logger.exception("Failed to build skill prompt for match %s", body.match_id)
        yield _format_sse_event(
            SSEEvent(
                type="error",
                content="Failed to load analysis skill. Please try again.",
            )
        )
        yield _format_done()
        return

    try:
        async for event in svc.stream_chat(
            messages,
            lang=body.lang,
        ):
            yield _format_sse_event(event)
    except Exception:
        logger.exception("Unexpected error in match analysis stream")
        yield _format_sse_event(
            SSEEvent(
                type="error",
                content="An unexpected error occurred during streaming.",
            )
        )

    yield _format_done()


async def _championship_analysis_stream(
    svc: AIService,
    body: ChampionshipAnalysisRequest,
) -> AsyncGenerator[str, None]:
    """Yield SSE-formatted strings for a championship prediction request.

    The pipeline is:
    1. Build the full prompt via ``PromptBuilder.build_championship_prompt``.
    2. Stream ``SSEEvent`` objects from ``AIService.stream_chat``.
    3. Convert each event to ``data: {json}\\n\\n``.
    4. Emit ``data: [DONE]\\n\\n`` on completion.

    Skill file loading failures are caught and surfaced as ``error`` events.
    """
    try:
        messages = PromptBuilder.build_championship_prompt(body)
    except Exception:
        logger.exception("Failed to build championship prompt")
        yield _format_sse_event(
            SSEEvent(
                type="error",
                content="Failed to load championship prediction skill. Please try again.",
            )
        )
        yield _format_done()
        return

    try:
        async for event in svc.stream_chat(
            messages,
            lang=body.lang,
        ):
            yield _format_sse_event(event)
    except Exception:
        logger.exception("Unexpected error in championship analysis stream")
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


@router.post(
    "/match-analysis",
    summary="AI match analysis (SSE streaming)",
)
async def match_analysis(
    body: MatchAnalysisRequest,
    svc: AIService = Depends(get_ai_service),
) -> "StreamingResponse":  # noqa: F821
    """Run a skill-driven match analysis and return the result as an SSE stream.

    Accepts a ``MatchAnalysisRequest`` body describing the match context,
    resolves the appropriate analysis skill, builds a reasoning-chain prompt,
    and streams the AI response using the same event format as ``/chat``.
    """
    from starlette.responses import StreamingResponse

    return StreamingResponse(
        _match_analysis_stream(svc, body),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/championship-analysis",
    summary="AI championship prediction (SSE streaming)",
)
async def championship_analysis(
    body: ChampionshipAnalysisRequest,
    svc: AIService = Depends(get_ai_service),
) -> "StreamingResponse":  # noqa: F821
    """Run a championship/runner-up prediction and return the result as an SSE stream.

    Accepts a ``ChampionshipAnalysisRequest`` body with language preference,
    loads the championship prediction skill (Monte Carlo simulation strategies),
    and streams the AI response using the same event format as ``/chat``.
    """
    from starlette.responses import StreamingResponse

    return StreamingResponse(
        _championship_analysis_stream(svc, body),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/skills",
    summary="List available AI analysis skills",
)
async def list_skills() -> ApiResponse[List[SkillInfo]]:
    """Return metadata for all registered AI analysis skills.

    No database query is performed — the data is read from the in-memory
    ``_SKILL_REGISTRY`` populated at module load time.
    """
    skills = PromptBuilder.get_available_skills()
    return ApiResponse(data=skills, message="ok")