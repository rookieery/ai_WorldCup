"""CORS middleware configuration.

Allowed origins are loaded from ``app.config.settings.CORS_ORIGINS`` so
that different environments (local, staging, production) can be configured
via environment variables without code changes.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


def add_cors_middleware(app: FastAPI) -> None:
    """Register CORS middleware on the FastAPI application instance."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
