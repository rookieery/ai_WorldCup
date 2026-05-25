"""Redis infrastructure package.

Exports:
    - ``init_redis_pool`` / ``close_redis_pool`` — lifecycle helpers called
      from the FastAPI lifespan.
    - ``get_redis`` — dependency injection provider.
    - ``is_redis_available`` — health-check helper.
    - ``RedisKeys`` — centralised key pattern definitions.
"""

from app.redis.client import (
    close_redis_pool,
    get_redis,
    init_redis_pool,
    is_redis_available,
)
from app.redis.keys import RedisKeys

__all__ = [
    "RedisKeys",
    "close_redis_pool",
    "get_redis",
    "init_redis_pool",
    "is_redis_available",
]
