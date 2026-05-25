"""Live match state management — Redis-backed real-time status with in-memory fallback.

Each live match stores its real-time state (status, scores, activity level) inside
a Redis HASH keyed by ``live:match:{match_id}``.  When Redis is unavailable the
service degrades transparently to a process-local ``dict``.

Status changes also trigger cache invalidation markers so that downstream consumers
(groups, bracket) know their cached data is stale.

Broadcast integration
---------------------
Every mutating operation (status / score / activity update) also pushes a
WebSocket event through the ``ConnectionManager`` singleton so that connected
clients receive updates in real time.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from redis.asyncio import Redis

from app.redis.keys import RedisKeys
from app.schemas.ws_schema import WSEventType

logger = logging.getLogger(__name__)

# ── In-memory fallback store (single-process dev only) ────────────────────

_memory_store: Dict[int, Dict[str, Any]] = {}

# ── Constants ─────────────────────────────────────────────────────────────

_VALID_STATUSES = {"upcoming", "live", "finished", "postponed"}
_CACHE_INVALIDATION_TTL = 300  # seconds — matches typical cache lifetime


class LiveService:
    """Manage real-time match state in Redis with graceful in-memory fallback.

    Parameters
    ----------
    redis:
        An optional ``redis.asyncio.Redis`` instance.  When ``None`` the
        service falls back to an in-memory ``dict``.
    """

    def __init__(self, redis: Optional[Redis] = None) -> None:
        self._redis = redis

    # ── public API ────────────────────────────────────────────────────────

    async def update_match_status(
        self, match_id: int, status: str
    ) -> Dict[str, Any]:
        """Update the status field for a match and return the full live state.

        Also broadcasts a ``match_start`` or ``match_end`` event via the
        WebSocket ``ConnectionManager``.

        Parameters
        ----------
        match_id:
            The match whose status is changing.
        status:
            One of ``upcoming``, ``live``, ``finished``, ``postponed``.

        Returns
        -------
        dict
            The complete live data after the update.
        """
        if status not in _VALID_STATUSES:
            raise ValueError(f"Invalid match status: {status!r}")

        if self._redis is not None:
            result = await self._update_status_redis(match_id, status)
        else:
            result = self._update_status_memory(match_id, status)

        # ── Broadcast WebSocket event ────────────────────────────────────
        if status == "live":
            await _broadcast_event(
                WSEventType.MATCH_START,
                {"match_id": match_id, "status": status},
            )
        elif status == "finished":
            await _broadcast_event(
                WSEventType.MATCH_END,
                {
                    "match_id": match_id,
                    "status": status,
                    "home_score": result.get("home_score", 0),
                    "away_score": result.get("away_score", 0),
                },
            )
            # A finished match may also update the bracket
            await _broadcast_event(
                WSEventType.BRACKET_UPDATE,
                {"match_id": match_id, "status": status},
            )

        return result

    async def update_score(
        self,
        match_id: int,
        home_score: int,
        away_score: int,
    ) -> Dict[str, Any]:
        """Update the score for a match and return the full live state.

        Also broadcasts a ``score_update`` event via the WebSocket
        ``ConnectionManager``.

        Negative scores are rejected.
        """
        if home_score < 0 or away_score < 0:
            raise ValueError("Scores must be non-negative")

        if self._redis is not None:
            result = await self._update_score_redis(
                match_id, home_score, away_score
            )
        else:
            result = self._update_score_memory(
                match_id, home_score, away_score
            )

        # ── Broadcast WebSocket event ────────────────────────────────────
        await _broadcast_event(
            WSEventType.SCORE_UPDATE,
            {
                "match_id": match_id,
                "home_score": home_score,
                "away_score": away_score,
            },
        )

        return result

    async def update_activity(
        self, match_id: int, level: int
    ) -> Dict[str, Any]:
        """Update the activity level for a match (0-100 scale).

        Also broadcasts an ``activity_update`` event via the WebSocket
        ``ConnectionManager``.

        The value is clamped to ``0..100``.
        """
        level = max(0, min(100, level))

        if self._redis is not None:
            result = await self._update_activity_redis(match_id, level)
        else:
            result = self._update_activity_memory(match_id, level)

        # ── Broadcast WebSocket event ────────────────────────────────────
        await _broadcast_event(
            WSEventType.ACTIVITY_UPDATE,
            {"match_id": match_id, "activity_level": level},
        )

        return result

    async def get_live_matches(self) -> List[Dict[str, Any]]:
        """Return the live data for all matches currently in ``live`` status.

        Returns a list of dicts, each containing at least ``match_id``,
        ``status``, ``home_score``, ``away_score``, and ``activity``.
        """
        if self._redis is not None:
            return await self._get_live_matches_redis()
        return self._get_live_matches_memory()

    async def get_match_live_data(
        self, match_id: int
    ) -> Optional[Dict[str, Any]]:
        """Return the real-time data for a single match, or ``None`` if absent.

        When Redis is available the data is read from the live hash.
        Otherwise the in-memory fallback is consulted.
        """
        if self._redis is not None:
            return await self._get_match_data_redis(match_id)
        return self._get_match_data_memory(match_id)

    # ── Redis implementations ───────────────────────────────────────────────

    async def _update_status_redis(
        self, match_id: int, status: str
    ) -> Dict[str, Any]:
        key = RedisKeys.LIVE_MATCH.format(match_id=match_id)
        async with self._redis.pipeline(transaction=True) as pipe:
            pipe.hset(key, "status", status)
            pipe.hgetall(key)
            _, data = await pipe.execute()

        await self._invalidate_cache()
        result = _hash_to_live_data(match_id, data)
        logger.info("Match %d status updated to %s (Redis)", match_id, status)
        return result

    async def _update_score_redis(
        self, match_id: int, home_score: int, away_score: int
    ) -> Dict[str, Any]:
        key = RedisKeys.LIVE_MATCH.format(match_id=match_id)
        async with self._redis.pipeline(transaction=True) as pipe:
            pipe.hset(
                key,
                mapping={
                    "home_score": str(home_score),
                    "away_score": str(away_score),
                },
            )
            pipe.hgetall(key)
            _, data = await pipe.execute()

        await self._invalidate_cache()
        result = _hash_to_live_data(match_id, data)
        logger.info(
            "Match %d score updated to %d-%d (Redis)",
            match_id,
            home_score,
            away_score,
        )
        return result

    async def _update_activity_redis(
        self, match_id: int, level: int
    ) -> Dict[str, Any]:
        key = RedisKeys.LIVE_MATCH.format(match_id=match_id)
        async with self._redis.pipeline(transaction=True) as pipe:
            pipe.hset(key, "activity", str(level))
            pipe.hgetall(key)
            _, data = await pipe.execute()

        result = _hash_to_live_data(match_id, data)
        logger.debug("Match %d activity updated to %d (Redis)", match_id, level)
        return result

    async def _get_live_matches_redis(self) -> List[Dict[str, Any]]:
        """Scan for all live:match:* keys and filter by status=live."""
        pattern = RedisKeys.LIVE_MATCH.format(match_id="*")
        keys: List[str] = []
        async for key in self._redis.scan_iter(match=pattern, count=100):
            keys.append(key)

        if not keys:
            return []

        results: List[Dict[str, Any]] = []
        for key in keys:
            data = await self._redis.hgetall(key)
            if data.get("status") == "live":
                match_id = _extract_match_id(key)
                results.append(_hash_to_live_data(match_id, data))

        return results

    async def _get_match_data_redis(
        self, match_id: int
    ) -> Optional[Dict[str, Any]]:
        key = RedisKeys.LIVE_MATCH.format(match_id=match_id)
        data = await self._redis.hgetall(key)
        if not data:
            return None
        return _hash_to_live_data(match_id, data)

    async def _invalidate_cache(self) -> None:
        """Set short-lived markers to signal downstream caches are stale."""
        try:
            ts = str(int(time.time()))
            await self._redis.set(
                RedisKeys.CACHE_GROUPS, ts, ex=_CACHE_INVALIDATION_TTL
            )
            await self._redis.set(
                RedisKeys.CACHE_BRACKET, ts, ex=_CACHE_INVALIDATION_TTL
            )
        except Exception:
            logger.warning(
                "Failed to update cache invalidation markers", exc_info=True
            )

    # ── In-memory fallback implementations ─────────────────────────────

    def _update_status_memory(
        self, match_id: int, status: str
    ) -> Dict[str, Any]:
        entry = _memory_store.setdefault(
            match_id, _default_live_entry(match_id)
        )
        entry["status"] = status
        logger.info(
            "Match %d status updated to %s (memory)", match_id, status
        )
        return dict(entry)

    def _update_score_memory(
        self, match_id: int, home_score: int, away_score: int
    ) -> Dict[str, Any]:
        entry = _memory_store.setdefault(
            match_id, _default_live_entry(match_id)
        )
        entry["home_score"] = home_score
        entry["away_score"] = away_score
        logger.info(
            "Match %d score updated to %d-%d (memory)",
            match_id,
            home_score,
            away_score,
        )
        return dict(entry)

    def _update_activity_memory(
        self, match_id: int, level: int
    ) -> Dict[str, Any]:
        entry = _memory_store.setdefault(
            match_id, _default_live_entry(match_id)
        )
        entry["activity"] = level
        logger.debug(
            "Match %d activity updated to %d (memory)", match_id, level
        )
        return dict(entry)

    @staticmethod
    def _get_live_matches_memory() -> List[Dict[str, Any]]:
        return [
            dict(entry)
            for entry in _memory_store.values()
            if entry.get("status") == "live"
        ]

    @staticmethod
    def _get_match_data_memory(match_id: int) -> Optional[Dict[str, Any]]:
        entry = _memory_store.get(match_id)
        return dict(entry) if entry else None


# ── Module-level helpers ──────────────────────────────────────────────


def _default_live_entry(match_id: int = 0) -> Dict[str, Any]:
    """Return a fresh live-data dict with sensible defaults."""
    return {
        "match_id": match_id,
        "status": "upcoming",
        "home_score": 0,
        "away_score": 0,
        "activity": 0,
    }


def _hash_to_live_data(
    match_id: int, data: Dict[str, str]
) -> Dict[str, Any]:
    """Convert a Redis HASH response (all strings) to a typed dict."""
    return {
        "match_id": match_id,
        "status": data.get("status", "upcoming"),
        "home_score": int(data.get("home_score", 0)),
        "away_score": int(data.get("away_score", 0)),
        "activity": int(data.get("activity", 0)),
    }


def _extract_match_id(key: str) -> int:
    """Extract the numeric match ID from a Redis key like ``live:match:42``."""
    try:
        return int(key.split(":")[-1])
    except (ValueError, IndexError):
        logger.warning("Could not extract match_id from key %r", key)
        return 0


async def _broadcast_event(
    event_type: WSEventType,
    data: Dict[str, Any],
) -> None:
    """Fire-and-forget broadcast through the WebSocket ConnectionManager.

    Imports are deferred to avoid circular dependencies at module load time.
    Broadcast failures are logged but never raise — the caller (e.g.
    LiveService) must not be disrupted by WebSocket issues.
    """
    try:
        from app.services.websocket_manager import get_manager

        manager = get_manager()
        await manager.broadcast(event_type, data)
    except Exception:
        logger.warning(
            "WebSocket broadcast failed for %s", event_type.value, exc_info=True
        )
