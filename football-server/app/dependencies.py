"""Dependency injection providers for FastAPI.

Centralises session management, service factory functions, and
language extraction so that controllers stay thin and consistent.
"""

from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Depends, Query, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.redis.client import get_redis

# ── Database session ────────────────────────────────────────────────────────

# The engine is created once inside ``main.py`` lifespan and stored here so
# that ``get_db`` can reference it without importing the application object.
_engine = None
_session_factory = None


def init_db_engine() -> None:
    """Create the global async engine and session factory.

    Called once during application startup (lifespan).
    """
    global _engine, _session_factory  # noqa: PLW0603
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.orm import sessionmaker

    _engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.is_development,
        pool_pre_ping=True,
    )
    _session_factory = sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def dispose_db_engine() -> None:
    """Dispose the global async engine.

    Called once during application shutdown (lifespan).
    """
    global _engine  # noqa: PLW0603
    if _engine is not None:
        await _engine.dispose()
        _engine = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an ``AsyncSession`` with automatic cleanup.

    Use as a FastAPI ``Depends`` in every route that needs DB access.
    """
    if _session_factory is None:
        raise RuntimeError(
            "Database session factory not initialised. "
            "Ensure init_db_engine() is called during app startup."
        )
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ── Language extraction ─────────────────────────────────────────────────────


def get_language(
    request: Request,
    lang: str = Query(default="en", description="Language: en or zh"),
) -> str:
    """Determine the response language from query param or Accept-Language header.

    Priority: explicit ``lang`` query parameter > ``Accept-Language`` header > ``en``.
    """
    if lang and lang.lower() in ("en", "zh"):
        return lang.lower()

    accept = request.headers.get("accept-language", "")
    if "zh" in accept.lower():
        return "zh"

    return "en"


# ── Service factories ──────────────────────────────────────────────────────


def get_team_service(session: AsyncSession = Depends(get_db)) -> "TeamService":
    """Create a ``TeamService`` with an injected session."""
    from app.services.team_service import TeamService

    return TeamService(session)


def get_match_service(
    session: AsyncSession = Depends(get_db),
    redis: Redis | None = Depends(get_redis),
) -> "MatchService":
    """Create a ``MatchService`` with an injected session and optional Redis."""
    from app.services.match_service import MatchService

    return MatchService(session, redis=redis)


def get_venue_service(session: AsyncSession = Depends(get_db)) -> "VenueService":
    """Create a ``VenueService`` with an injected session."""
    from app.services.venue_service import VenueService

    return VenueService(session)


def get_group_service(session: AsyncSession = Depends(get_db)) -> "GroupService":
    """Create a ``GroupService`` with an injected session."""
    from app.services.group_service import GroupService

    return GroupService(session)


def get_bracket_service(session: AsyncSession = Depends(get_db)) -> "BracketService":
    """Create a ``BracketService`` with an injected session."""
    from app.services.bracket_service import BracketService

    return BracketService(session)


def get_ai_service() -> "AIService":
    """Create an ``AIService`` (no DB session needed — pure HTTP client)."""
    from app.services.ai_service import AIService

    return AIService()


def get_feishu_client() -> "FeishuClient":
    """Create or return the shared ``FeishuClient`` singleton."""
    from app.services.feishu_client import FeishuClient

    return FeishuClient()
