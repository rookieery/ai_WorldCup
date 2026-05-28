"""Seed script: insert all 16 host-city venues for the 2026 FIFA World Cup.

Supports idempotent execution -- existing venues (matched by ``name``) are
updated in-place rather than causing duplicate-key errors.

Usage::

    cd football-server
    python -m scripts.seed_venues
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from scripts.venue_data import VENUES

logger = logging.getLogger(__name__)


async def seed_venues(session: AsyncSession) -> dict[str, int]:
    """Insert or update all 16 venues.

    Returns a summary dict with ``inserted``, ``updated``, and ``skipped``
    counts.
    """

    from app.models.venue import Venue

    inserted = 0
    updated = 0
    skipped = 0

    for venue_data in VENUES:
        name = venue_data["name"]
        stmt = select(Venue).where(Venue.name == name)
        result = await session.execute(stmt)
        existing = result.unique().scalar_one_or_none()

        if existing is None:
            venue = Venue(**venue_data)
            session.add(venue)
            inserted += 1
            logger.debug("Inserted venue %s (%s)", name, venue_data["city"])
        else:
            changed = False
            for key, value in venue_data.items():
                if getattr(existing, key, None) != value:
                    setattr(existing, key, value)
                    changed = True
            if changed:
                updated += 1
                logger.debug("Updated venue %s (%s)", name, venue_data["city"])
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
            result = await seed_venues(session)

    await engine.dispose()

    total = result["inserted"] + result["updated"] + result["skipped"]
    logger.info(
        "Seed complete: %d venues processed (inserted=%d, updated=%d, skipped=%d)",
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
