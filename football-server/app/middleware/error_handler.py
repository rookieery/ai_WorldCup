"""Global exception handler middleware.

Converts all raised exceptions into a unified ApiResponse JSON shape:
    {"code": int, "data": null, "message": str}

Custom ``AppException`` subclasses carry their own status code and message.
Unexpected exceptions are logged and return a generic 500 response.
"""

from __future__ import annotations

import logging
import traceback

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import RequestResponseEndpoint, BaseHTTPMiddleware

from app.exceptions import AppException

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Starlette middleware that catches all unhandled exceptions."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        try:
            return await call_next(request)
        except AppException as exc:
            logger.warning(
                "AppException [%d] %s — %s %s",
                exc.code,
                exc.message,
                request.method,
                request.url.path,
            )
            return JSONResponse(
                status_code=exc.code,
                content={"code": exc.code, "data": None, "message": exc.message},
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Unhandled exception — %s %s\n%s",
                request.method,
                request.url.path,
                traceback.format_exc(),
            )
            return JSONResponse(
                status_code=500,
                content={
                    "code": 500,
                    "data": None,
                    "message": "Internal server error",
                },
            )
