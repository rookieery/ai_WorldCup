"""Seed script: insert all 48 participating teams for the 2026 FIFA World Cup.

Supports idempotent execution -- existing teams (matched by ``code``) are
updated in-place rather than causing duplicate-key errors.

Usage::

    cd football-server
    python -m scripts.seed_teams
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from scripts.team_data import TEAMS

logger = logging.getLogger(__name__)


async def seed_teams(session: AsyncSession) -> dict[str, int]:
    """Insert or update all 48 teams.

    Returns a summary dict with ``inserted``, ``updated``, and ``skipped``
    counts.
    """

    from app.models.team import Team

    inserted = 0
    updated = 0
    skipped = 0

    for team_data in TEAMS:
        code = team_data["code"]
        stmt = select(Team).where(Team.code == code)
        result = await session.execute(stmt)
        existing = result.unique().scalar_one_or_none()

        if existing is None:
            team = Team(**team_data)
            session.add(team)
            inserted += 1
            logger.debug("Inserted team %s (%s)", code, team_data["name"])
        else:
            changed = False
            for key, value in team_data.items():
                if getattr(existing, key, None) != value:
                    setattr(existing, key, value)
                    changed = True
            if changed:
                updated += 1
                logger.debug("Updated team %s (%s)", code, team_data["name"])
            else:
                skipped += 1

    await session.flush()

    return {"inserted": inserted, "updated": updated, "skipped": skipped}


async def run() -> None:
    """Create an async session, run the seed, and print a summary."""

    from app.models.base import Base

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        async with session.begin():
            result = await seed_teams(session)

    await engine.dispose()

    total = result["inserted"] + result["updated"] + result["skipped"]
    logger.info(
        "Seed complete: %d teams processed (inserted=%d, updated=%d, skipped=%d)",
        total,
        result["inserted"],
        result["updated"],
        result["skipped"],
    )


def main() -> None:
    """CLI entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    asyncio.run(run())


if __name__ == "__main__":
    main()