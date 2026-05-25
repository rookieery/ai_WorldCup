"""Redis connection pool manager with graceful degradation.

Provides an async Redis client via a module-level pool that is initialised
during application startup and torn down on shutdown.  When Redis is
disabled (``REDIS_ENABLED=false``) or the connection fails, all operations
fall back silently so the rest of the application is never blocked.

Typical usage in a FastAPI dependency::

    from app.redis.client import get_redis

    async def my_service(redis: Redis = Depends(get_redis)):
        if redis is None:
            # Redis unavailable — use local fallback
            ...
"""

from __future__ import annotations

import logging
from typing import Optional

import redis.asyncio as aioredis
from redis.asyncio import Redis
from redis.asyncio.connection import ConnectionPool

from app.config import settings

logger = logging.getLogger(__name__)

# ── Module-level pool singleton ────────────────────────────────────────────

_pool: Optional[ConnectionPool] = None
_redis: Optional[Redis] = None
_available: bool = False


async def init_redis_pool() -> None:
    """Create the connection pool and verify connectivity.

    Safe to call even when ``REDIS_ENABLED`` is ``False`` — in that case
    the function returns immediately without touching the network.
    """
    global _pool, _redis, _available  # noqa: PLW0603

    if not settings.REDIS_ENABLED:
        logger.info("Redis is disabled via REDIS_ENABLED=false — skipping pool init")
        _available = False
        return

    try:
        _pool = ConnectionPool.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=10,
        )
        _redis = Redis(connection_pool=_pool)

        # Verify connectivity before marking as available
        await _redis.ping()
        _available = True
        logger.info("Redis connection pool initialised (%s)", settings.REDIS_URL)
    except Exception:
        _available = False
        _pool = None
        _redis = None
        logger.warning(
            "Redis connection failed — operating in degraded mode. "
            "Features requiring Redis will use fallbacks.",
            exc_info=True,
        )


async def close_redis_pool() -> None:
    """Gracefully close the connection pool on application shutdown."""
    global _pool, _redis, _available  # noqa: PLW0603

    if _redis is not None:
        await _redis.aclose()
    if _pool is not None:
        await _pool.aclose()

    _pool = None
    _redis = None
    _available = False
    logger.info("Redis connection pool closed")


# ── FastAPI dependency ─────────────────────────────────────────────────────


def get_redis() -> Optional[Redis]:
    """Return the shared ``Redis`` instance, or ``None`` when unavailable.

    Use as a FastAPI ``Depends`` in routes that optionally need Redis::

        @router.get("/example")
        async def example(redis: Optional[Redis] = Depends(get_redis)):
            if redis is None:
                return {"source": "fallback"}
            ...
    """
    return _redis if _available else None


def is_redis_available() -> bool:
    """Return ``True`` if the Redis pool is healthy and ready for use."""
    return _available
