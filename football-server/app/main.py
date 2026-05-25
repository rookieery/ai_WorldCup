"""FastAPI application factory.

Creates the application instance, registers lifespan hooks for DB engine
initialisation, mounts all middleware and routers, and exposes /docs.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import logging

from fastapi import FastAPI

from app.config import settings
from app.dependencies import dispose_db_engine, init_db_engine
from app.redis import close_redis_pool, init_redis_pool

logger = logging.getLogger(__name__)


# ── Lifespan ────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: initialise resources on startup, clean up on shutdown."""
    logger.info("Starting Football World Cup API (%s)", settings.APP_ENV)
    init_db_engine()
    await init_redis_pool()
    yield
    logger.info("Shutting down — disposing database engine")
    await close_redis_pool()
    await dispose_db_engine()


# ── Application factory ────────────────────────────────────────────────────


def create_app() -> FastAPI:
    """Build and return the fully configured FastAPI application."""
    application = FastAPI(
        title="Football World Cup 2026 API",
        description=(
            "Backend API for the FIFA World Cup 2026 Dashboard. "
            "Provides match data, group standings, knockout bracket, "
            "team info, venue details, and AI-powered analysis."
        ),
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── Middleware (order matters — last added runs first) ───────────
    from app.middleware import ErrorHandlerMiddleware, LoggingMiddleware, add_cors_middleware

    application.add_middleware(ErrorHandlerMiddleware)
    application.add_middleware(LoggingMiddleware)
    add_cors_middleware(application)

    # ── Routers ──────────────────────────────────────────────────────
    from app.controllers import (
        ai_router,
        bracket_router,
        cheer_router,
        group_router,
        match_router,
        team_router,
        venue_router,
        ws_router,
    )

    application.include_router(match_router)
    application.include_router(team_router)
    application.include_router(venue_router)
    application.include_router(group_router)
    application.include_router(bracket_router)
    application.include_router(cheer_router)
    application.include_router(ws_router)
    application.include_router(ai_router)

    return application


app = create_app()
