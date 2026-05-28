"""Cheer (fan voting) business logic — Redis-backed atomic counters with in-memory fallback.

Each match stores two counters (``home`` and ``away``) inside a Redis HASH keyed
by ``cheers:match:{match_id}``.  When Redis is unavailable the service degrades
transparently to a process-local ``dict`` — suitable for single-process
development only.

Duplicate-vote prevention uses IP-based rate limiting: a single IP may vote at
most once per match within a configurable cooldown window.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from redis.asyncio import Redis

from app.redis.keys import RedisKeys
from app.schemas.cheer_schema import CheerResponse

logger = logging.getLogger(__name__)

# ── IP rate-limit constants ──────────────────────────────────────────────────

_RATE_LIMIT_SECONDS: int = 60 * 5  # 5-minute cooldown per (IP, match)
_RATE_LIMIT_KEY: str = "cheer:ratelimit:{match_id}:{ip}"


class CheerService:
    """Manage fan cheer counts with atomic increments and IP-based deduplication.

    Parameters
    ----------
    redis:
        An optional ``redis.asyncio.Redis`` instance.  When ``None`` the
        service falls back to an in-memory ``dict``.

    Note
    ----
    The in-memory fallback stores are **class-level** so that state persists
    across per-request service instances.  This is only suitable for
    single-process development.
    """

    # Class-level shared stores for in-memory fallback (single-process only)
    _shared_counts: dict[int, dict[str, int]] = {}
    _shared_rate_limits: dict[str, float] = {}

    def __init__(self, redis: Optional[Redis] = None) -> None:
        self._redis = redis

    # ── public API ─────────────────────────────────────────────────────────

    async def get_cheers(self, match_id: int) -> CheerResponse:
        """Return the current cheer counts for *match_id*.

        Returns ``{home: 0, away: 0}`` when no votes have been cast.
        """
        if self._redis is not None:
            return await self._get_cheers_redis(match_id)
        return self._get_cheers_memory(match_id)

    async def vote_cheer(
        self,
        match_id: int,
        side: str,
        client_ip: str,
    ) -> CheerResponse:
        """Record a cheer vote and return the updated counts.

        Parameters
        ----------
        match_id:
            The match to vote on.
        side:
            ``"home"`` or ``"away"``.
        client_ip:
            Caller IP used for rate-limiting.

        Raises
        ------
        BusinessError
            If the caller has already voted within the cooldown window.
        """
        from app.exceptions import BusinessError

        rate_key = _RATE_LIMIT_KEY.format(match_id=match_id, ip=client_ip)

        # ── Rate-limit check ──────────────────────────────────────────────
        if self._redis is not None:
            voted = await self._redis.exists(rate_key)
            if voted:
                raise BusinessError(message="Already voted — please wait before voting again")
        else:
            last_ts = self._shared_rate_limits.get(rate_key)
            if last_ts and (time.monotonic() - last_ts) < _RATE_LIMIT_SECONDS:
                raise BusinessError(message="Already voted — please wait before voting again")

            # Purge expired rate-limit entries periodically (every 100 calls)
            self._cleanup_expired_rate_limits()

        # ── Increment counter atomically ──────────────────────────────────
        if self._redis is not None:
            result = await self._vote_redis(match_id, side, rate_key)
        else:
            result = self._vote_memory(match_id, side, rate_key)

        return result

    # ── Redis implementations ──────────────────────────────────────────────

    async def _get_cheers_redis(self, match_id: int) -> CheerResponse:
        key = RedisKeys.CHEERS_MATCH.format(match_id=match_id)
        data = await self._redis.hgetall(key)
        return CheerResponse(
            match_id=match_id,
            home=int(data.get("home", 0)),
            away=int(data.get("away", 0)),
        )

    async def _vote_redis(
        self,
        match_id: int,
        side: str,
        rate_key: str,
    ) -> CheerResponse:
        key = RedisKeys.CHEERS_MATCH.format(match_id=match_id)

        # Atomic increment via pipeline
        async with self._redis.pipeline(transaction=True) as pipe:
            pipe.hincrby(key, side, 1)
            pipe.hgetall(key)
            _, data = await pipe.execute()

        # Set rate-limit key with TTL
        await self._redis.set(rate_key, "1", ex=_RATE_LIMIT_SECONDS)

        return CheerResponse(
            match_id=match_id,
            home=int(data.get("home", 0)),
            away=int(data.get("away", 0)),
        )

    # ── In-memory fallback implementations ─────────────────────────────────

    def _get_cheers_memory(self, match_id: int) -> CheerResponse:
        counts = self._shared_counts.get(match_id, {"home": 0, "away": 0})
        return CheerResponse(
            match_id=match_id,
            home=counts.get("home", 0),
            away=counts.get("away", 0),
        )

    def _vote_memory(
        self,
        match_id: int,
        side: str,
        rate_key: str,
    ) -> CheerResponse:
        if match_id not in self._shared_counts:
            self._shared_counts[match_id] = {"home": 0, "away": 0}

        self._shared_counts[match_id][side] += 1
        self._shared_rate_limits[rate_key] = time.monotonic()

        counts = self._shared_counts[match_id]
        return CheerResponse(
            match_id=match_id,
            home=counts["home"],
            away=counts["away"],
        )

    @classmethod
    def _cleanup_expired_rate_limits(cls) -> None:
        """Remove expired in-memory rate-limit entries to prevent unbounded growth."""
        now = time.monotonic()
        expired = [
            k for k, ts in cls._shared_rate_limits.items()
            if (now - ts) >= _RATE_LIMIT_SECONDS
        ]
        for k in expired:
            del cls._shared_rate_limits[k]
