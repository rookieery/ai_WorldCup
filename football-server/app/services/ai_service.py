"""AI chat service — Deepseek API client with SSE streaming.

Provides the core ``stream_chat`` async generator that calls the Deepseek
V4 Pro model (OpenAI-compatible), parses the streaming response into
structured ``SSEEvent`` objects (thinking / answer / analysis / done / error),
and gracefully handles timeouts and API rate-limits.
"""

from __future__ import annotations

import json
import logging
from typing import AsyncGenerator, Dict, List, Literal, Optional

import httpx

from app.config import settings
from app.schemas.ai_schema import SSEEvent

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEEPSEEK_CHAT_PATH = "/chat/completions"
_DEFAULT_MODEL = "deepseek-v4-pro"
_TIMEOUT_SECONDS = 30.0

# Patterns that indicate the user is requesting a structured team analysis
_ANALYSIS_KEYWORDS: Dict[str, List[str]] = {
    "zh-CN": ["分析", "评估", "雷达", "概率", "预测"],
    "en-US": ["analysis", "evaluate", "radar", "probability", "predict"],
}

# Error messages (bilingual)
_ERROR_MESSAGES: Dict[str, Dict[str, str]] = {
    "rate_limit": {
        "zh-CN": "AI 服务当前请求过多，请稍后再试。",
        "en-US": "AI service is currently overloaded. Please try again later.",
    },
    "timeout": {
        "zh-CN": "AI 服务响应超时，请稍后再试。",
        "en-US": "AI service timed out. Please try again later.",
    },
    "generic": {
        "zh-CN": "AI 服务暂时不可用，请稍后再试。",
        "en-US": "AI service is temporarily unavailable. Please try again later.",
    },
    "no_key": {
        "zh-CN": "AI 服务未配置 API 密钥。",
        "en-US": "AI service API key is not configured.",
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_analysis_request(text: str, lang: str) -> bool:
    """Return True if the user message looks like a structured analysis request."""
    keywords = _ANALYSIS_KEYWORDS.get(lang, _ANALYSIS_KEYWORDS["en-US"])
    return any(kw in text.lower() for kw in keywords)


def _error_event(key: str, lang: str) -> SSEEvent:
    """Create an SSE error event from a predefined message key."""
    messages = _ERROR_MESSAGES.get(key, _ERROR_MESSAGES["generic"])
    return SSEEvent(type="error", content=messages.get(lang, messages["en-US"]))


def _parse_sse_line(line: str) -> Optional[Dict]:
    """Parse a single ``data: {...}`` line from the SSE stream.

    Returns the parsed dict, ``None`` for keep-alive comments, or raises
    ``ValueError`` on malformed JSON.
    """
    if line.startswith("data: "):
        payload = line[len("data: "):].strip()
        if payload == "[DONE]":
            return None
        return json.loads(payload)
    # Lines starting with ``:`` are SSE comments (keep-alive) — skip.
    return None


def _extract_analysis_from_answer(answer_text: str) -> Optional[Dict]:
    """Try to extract a JSON team analysis object from the full answer text.

    The AI model may embed a JSON block in its response.  We look for the
    outermost ``{`` … ``}`` that contains a ``team_code`` key, indicating a
    valid ``TeamAnalysisResponse`` payload.
    """
    try:
        # Fast path — the whole answer might be JSON
        data = json.loads(answer_text)
        if isinstance(data, dict) and "team_code" in data:
            return data
    except (json.JSONDecodeError, ValueError):
        pass

    # Slow path — search for an embedded JSON block
    start = answer_text.find("{")
    while start != -1:
        # Find matching closing brace (naive but good enough for well-formed JSON)
        depth = 0
        for i in range(start, len(answer_text)):
            if answer_text[i] == "{":
                depth += 1
            elif answer_text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        candidate = json.loads(answer_text[start : i + 1])
                        if isinstance(candidate, dict) and "team_code" in candidate:
                            return candidate
                    except (json.JSONDecodeError, ValueError):
                        pass
                    break
        start = answer_text.find("{", start + 1)

    return None


# ---------------------------------------------------------------------------
# AIService
# ---------------------------------------------------------------------------


class AIService:
    """Deepseek API client that streams chat completions as ``SSEEvent`` objects.

    Usage::

        service = AIService()
        async for event in service.stream_chat(messages, context, lang):
            handle(event)  # SSEEvent with type / content / data
    """

    def __init__(self) -> None:
        self._api_key: str = settings.DEEPSEEK_API_KEY
        self._base_url: str = settings.DEEPSEEK_BASE_URL.rstrip("/")
        self._model: str = _DEFAULT_MODEL
        self._client: Optional[httpx.AsyncClient] = None

    # -- Client lifecycle ----------------------------------------------------

    def _get_client(self) -> httpx.AsyncClient:
        """Lazily create (or return the existing) ``httpx.AsyncClient``."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(_TIMEOUT_SECONDS),
            )
        return self._client

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    # -- Core streaming method -----------------------------------------------

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        *,
        context: Optional[Dict] = None,
        lang: Literal["zh-CN", "en-US"] = "zh-CN",
    ) -> AsyncGenerator[SSEEvent, None]:
        """Call the Deepseek API and yield ``SSEEvent`` objects.

        Parameters
        ----------
        messages:
            OpenAI-compatible message list ``[{"role": ..., "content": ...}]``.
        context:
            Optional client-side context (unused for now, reserved for future
            personalisation).
        lang:
            Language for error messages and analysis keyword detection.

        Yields
        ------
        SSEEvent
            Events with type ``thinking``, ``answer``, ``analysis``, ``error``,
            or ``done``.
        """
        # Guard: no API key configured
        if not self._api_key:
            yield _error_event("no_key", lang)
            yield SSEEvent(type="done")
            return

        # Detect if user is asking for analysis
        last_user_msg = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break
        wants_analysis = _is_analysis_request(last_user_msg, lang)

        client = self._get_client()
        payload = {
            "model": self._model,
            "messages": messages,
            "stream": True,
        }

        answer_buffer: list[str] = []

        try:
            async with client.stream(
                "POST",
                _DEEPSEEK_CHAT_PATH,
                json=payload,
            ) as response:
                if response.status_code == 429:
                    yield _error_event("rate_limit", lang)
                    yield SSEEvent(type="done")
                    return

                if response.status_code >= 400:
                    body = await response.aread()
                    logger.warning(
                        "Deepseek API error %d: %s",
                        response.status_code,
                        body.decode("utf-8", errors="replace")[:500],
                    )
                    yield _error_event("generic", lang)
                    yield SSEEvent(type="done")
                    return

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue

                    try:
                        chunk = _parse_sse_line(line)
                    except (json.JSONDecodeError, ValueError):
                        # Skip malformed lines silently
                        continue

                    if chunk is None:
                        # [DONE] received from upstream
                        break

                    choices = chunk.get("choices", [])
                    if not choices:
                        continue

                    delta = choices[0].get("delta", {})

                    # Reasoning / thinking content
                    reasoning_delta = delta.get("reasoning_content")
                    if reasoning_delta:
                        yield SSEEvent(type="thinking", content=reasoning_delta)

                    # Answer content
                    content_delta = delta.get("content")
                    if content_delta:
                        answer_buffer.append(content_delta)
                        yield SSEEvent(type="answer", content=content_delta)

        except httpx.TimeoutException:
            logger.warning("Deepseek API request timed out after %.0fs", _TIMEOUT_SECONDS)
            yield _error_event("timeout", lang)
            yield SSEEvent(type="done")
            return
        except httpx.HTTPStatusError as exc:
            logger.warning("Deepseek HTTP error: %s", exc)
            yield _error_event("generic", lang)
            yield SSEEvent(type="done")
            return
        except Exception:
            logger.exception("Unexpected error during Deepseek streaming")
            yield _error_event("generic", lang)
            yield SSEEvent(type="done")
            return

        # Post-stream: if the user requested analysis and we accumulated answer
        # text, attempt to extract a structured analysis payload.
        if wants_analysis and answer_buffer:
            full_answer = "".join(answer_buffer)
            analysis_data = _extract_analysis_from_answer(full_answer)
            if analysis_data is not None:
                yield SSEEvent(type="analysis", data=analysis_data)

        yield SSEEvent(type="done")