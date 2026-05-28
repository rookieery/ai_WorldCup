"""Request logging middleware.

Records method, path, response status, and elapsed duration for every
incoming HTTP request using the standard ``logging`` module.
"""

from __future__ import annotations

import logging
import time

from fastapi import Request, Response
from starlette.middleware.base import RequestResponseEndpoint, BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs request/response metadata."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start = time.perf_counter()

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s → %s (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
