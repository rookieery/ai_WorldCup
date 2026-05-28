"""One-click database initialization for the 2026 FIFA World Cup.

Seeds all data in the correct order:

1. Venues  (16 stadiums)
2. Teams   (48 national teams)
3. Matches (104 fixtures: 72 group + 32 knockout)
4. Bracket linkage (R32 -> R16 -> QF -> SF -> 3rd -> F)
5. Group standings (48 initial records, all zeros)

Supports idempotent execution -- re-running will verify / update data
without duplicating records.

Usage::

    cd football-server
    python -m scripts.seed_data
"""

from __future__ import annotations

import asyncio
import logging
import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)


# ── Step 5: Group standings init ────────────────────────────────────────────


async def _init_group_standings(session: AsyncSession) -> dict[str, int]:
    """Create 48 group_standings rows (one per team, all zeros).

    Returns ``{inserted: int, skipped: int}``.
    """
    from app.models.group_standing import GroupStanding
    from app.models.team import Team

    result = await session.execute(select(Team).where(Team.code != "TBD"))
    teams = result.unique().scalars().all()

    expected = 48
    if len(teams) != expected:
        raise ValueError(
            f"Expected {expected} non-TBD teams, found {len(teams)}. "
            "Run seed_teams first."
        )

    inserted = 0
    skipped = 0

    for team in teams:
        stmt = select(GroupStanding).where(GroupStanding.team_id == team.id)
        existing = (await session.execute(stmt)).unique().scalar_one_or_none()

        if existing is not None:
            skipped += 1
            continue

        standing = GroupStanding(
            team_id=team.id,
            group_label=team.group_label,
            played=0,
            won=0,
            drawn=0,
            lost=0,
            goals_for=0,
            goals_against=0,
            goal_difference=0,
            points=0,
            position=0,
        )
        session.add(standing)
        inserted += 1

    await session.flush()

    logger.info(
        "Group standings: inserted=%d, skipped=%d", inserted, skipped,
    )
    return {"inserted": inserted, "skipped": skipped}


# ── Orchestrator ────────────────────────────────────────────────────────────


async def run() -> None:
    """Execute the full seed pipeline and print a summary."""
    from app.models.base import Base
    from scripts.generate_bracket import generate_bracket
    from scripts.seed_matches import seed_matches
    from scripts.seed_teams import seed_teams
    from scripts.seed_venues import seed_venues

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    t0 = time.perf_counter()

    async with session_factory() as session:
        async with session.begin():
            logger.info("Step 1/5: Seeding venues...")
            venues = await seed_venues(session)

            logger.info("Step 2/5: Seeding teams...")
            teams = await seed_teams(session)

            logger.info("Step 3/5: Seeding matches...")
            matches = await seed_matches(session)

            logger.info("Step 4/5: Generating bracket linkage...")
            bracket = await generate_bracket(session)

            logger.info("Step 5/5: Initializing group standings...")
            standings = await _init_group_standings(session)

    await engine.dispose()

    elapsed = time.perf_counter() - t0

    # ── Pretty summary ────────────────────────────────────────────────────
    _print_summary(venues, teams, matches, bracket, standings, elapsed)


def _print_summary(
    venues: dict,
    teams: dict,
    matches: dict,
    bracket: dict,
    standings: dict,
    elapsed: float,
) -> None:
    """Log a human-readable seed summary."""

    def _total(d: dict) -> int:
        return d.get("inserted", 0) + d.get("updated", 0) + d.get("skipped", 0)

    v_total = _total(venues)
    t_total = _total(teams)
    m_total = _total(matches)

    logger.info("=" * 60)
    logger.info("  SEED DATA COMPLETE  (%.2fs)", elapsed)
    logger.info("=" * 60)
    logger.info(
        "  Venues:    %2d  (ins=%d, upd=%d, skip=%d)",
        v_total,
        venues["inserted"],
        venues.get("updated", 0),
        venues.get("skipped", 0),
    )
    logger.info(
        "  Teams:     %2d  (ins=%d, upd=%d, skip=%d)",
        t_total,
        teams["inserted"],
        teams.get("updated", 0),
        teams.get("skipped", 0),
    )
    logger.info(
        "  Matches:  %3d  (group=%d, knockout=%d, ins=%d, upd=%d, skip=%d)",
        m_total,
        matches.get("group_stage", m_total),
        matches.get("knockout", 0),
        matches["inserted"],
        matches.get("updated", 0),
        matches.get("skipped", 0),
    )
    logger.info(
        "  Bracket:   %2d matches, %d links verified, %d corrected",
        bracket["total_matches"],
        bracket["verified"],
        bracket["corrected"],
    )
    logger.info(
        "  Standings: %2d rows  (ins=%d, skip=%d)",
        standings["inserted"] + standings["skipped"],
        standings["inserted"],
        standings["skipped"],
    )
    logger.info("=" * 60)


# ── CLI entry point ─────────────────────────────────────────────────────────


def main() -> None:
    """CLI entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    asyncio.run(run())


if __name__ == "__main__":
    main()
