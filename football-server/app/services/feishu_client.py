"""Async HTTP client for Feishu (Lark) Open API.

Handles tenant_access_token lifecycle (fetch, cache, refresh) and
provides methods for sending / replying interactive card messages.

Mirrors the ``AIService`` pattern of lazy ``httpx.AsyncClient`` init.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, Optional

import httpx
from redis.asyncio import Redis

from app.config import settings

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

_BASE_URL = "https://open.feishu.cn/open-apis"
_TOKEN_URL = f"{_BASE_URL}/auth/v3/tenant_access_token/internal"
_SEND_MSG_URL = f"{_BASE_URL}/im/v1/messages"
_REDIS_TOKEN_KEY = "feishu:tenant_token"
_TOKEN_CACHE_SECONDS = 7000  # token expires at 7200s; refresh earlier


class FeishuClient:
    """Low-level Feishu Open API client with token management."""

    def __init__(self) -> None:
        self._client: Optional[httpx.AsyncClient] = None
        self._cached_token: str = ""
        self._token_expires_at: float = 0.0

    # ── HTTP client lifecycle ────────────────────────────────────────────

    def _get_client(self) -> httpx.AsyncClient:
        """Lazy-create the shared ``httpx.AsyncClient``."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    # ── Token management ─────────────────────────────────────────────────

    async def get_tenant_token(self, redis: Optional[Redis] = None) -> str:
        """Return a valid ``tenant_access_token``.

        Lookup order:
        1. In-memory cache (if still fresh)
        2. Redis cache (if available)
        3. Fetch new token from Feishu API
        """
        # 1. In-memory cache
        if self._cached_token and time.monotonic() < self._token_expires_at:
            return self._cached_token

        # 2. Redis cache
        if redis is not None:
            try:
                cached = await redis.get(_REDIS_TOKEN_KEY)
                if cached:
                    token = cached if isinstance(cached, str) else cached.decode()
                    self._cached_token = token
                    self._token_expires_at = time.monotonic() + _TOKEN_CACHE_SECONDS
                    return token
            except Exception:
                logger.warning("Redis token lookup failed", exc_info=True)

        # 3. Fetch new
        return await self._fetch_token(redis)

    async def _fetch_token(self, redis: Optional[Redis] = None) -> str:
        """Fetch a fresh ``tenant_access_token`` from Feishu and cache it."""
        client = self._get_client()
        resp = await client.post(
            _TOKEN_URL,
            json={
                "app_id": settings.FEISHU_APP_ID,
                "app_secret": settings.FEISHU_APP_SECRET,
            },
        )
        resp.raise_for_status()
        data = resp.json()

        code = data.get("code", -1)
        if code != 0:
            raise RuntimeError(
                f"Feishu token request failed: code={code}, msg={data.get('msg')}"
            )

        token: str = data["tenant_access_token"]
        expire: int = data.get("expire", _TOKEN_CACHE_SECONDS)

        # Cache in memory
        self._cached_token = token
        self._token_expires_at = time.monotonic() + min(expire, _TOKEN_CACHE_SECONDS)

        # Cache in Redis
        if redis is not None:
            try:
                await redis.set(_REDIS_TOKEN_KEY, token, ex=min(expire, _TOKEN_CACHE_SECONDS))
            except Exception:
                logger.warning("Redis token cache write failed", exc_info=True)

        logger.info("Feishu tenant_access_token refreshed (expires in %ds)", expire)
        return token

    # ── Message sending ──────────────────────────────────────────────────

    async def _ensure_auth_header(
        self,
        headers: Dict[str, str],
        redis: Optional[Redis] = None,
    ) -> Dict[str, str]:
        """Inject the Bearer authorization header, refreshing token on 401."""
        token = await self.get_tenant_token(redis)
        headers["Authorization"] = f"Bearer {token}"
        return headers

    async def send_card_message(
        self,
        receive_id: str,
        card_content: Dict[str, Any],
        *,
        receive_id_type: str = "chat_id",
        redis: Optional[Redis] = None,
    ) -> Dict[str, Any]:
        """Send an interactive card message to a Feishu chat.

        Args:
            receive_id: Target chat_id / open_id / user_id.
            card_content: The card JSON dict (already built).
            receive_id_type: ``"chat_id"`` | ``"open_id"`` | ``"user_id"``.
            redis: Optional Redis for token caching.

        Returns:
            Feishu API response body as a dict.
        """
        headers = {"Content-Type": "application/json; charset=utf-8"}
        await self._ensure_auth_header(headers, redis)

        params = {"receive_id_type": receive_id_type}
        body = {
            "receive_id": receive_id,
            "msg_type": "interactive",
            "content": json.dumps(card_content, ensure_ascii=False),
        }

        return await self._do_post(_SEND_MSG_URL, headers, params, body, redis)

    async def reply_message(
        self,
        message_id: str,
        card_content: Dict[str, Any],
        *,
        redis: Optional[Redis] = None,
    ) -> Dict[str, Any]:
        """Reply to a specific Feishu message with a card.

        Args:
            message_id: The message ID to reply to.
            card_content: The card JSON dict.
            redis: Optional Redis for token caching.

        Returns:
            Feishu API response body as a dict.
        """
        headers = {"Content-Type": "application/json; charset=utf-8"}
        await self._ensure_auth_header(headers, redis)

        url = f"{_SEND_MSG_URL}/{message_id}/reply"
        body = {
            "msg_type": "interactive",
            "content": json.dumps(card_content, ensure_ascii=False),
        }

        return await self._do_post(url, headers, {}, body, redis)

    # ── Internal helpers ─────────────────────────────────────────────────

    async def _do_post(
        self,
        url: str,
        headers: Dict[str, str],
        params: Dict[str, str],
        body: Dict[str, Any],
        redis: Optional[Redis],
        _retry: bool = True,
    ) -> Dict[str, Any]:
        """Execute a POST with automatic token refresh on 401."""
        client = self._get_client()
        resp = await client.post(url, headers=headers, params=params, json=body)

        if resp.status_code == 401 and _retry:
            logger.info("Feishu token expired, refreshing and retrying")
            # Force-refresh token
            self._cached_token = ""
            self._token_expires_at = 0.0
            await self._ensure_auth_header(headers, redis)
            return await self._do_post(url, headers, params, body, redis, _retry=False)

        resp.raise_for_status()
        result = resp.json()

        code = result.get("code", 0)
        if code != 0:
            logger.warning(
                "Feishu API returned non-zero code: code=%s, msg=%s",
                code,
                result.get("msg"),
            )

        return result
