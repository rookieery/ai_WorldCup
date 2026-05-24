"""Generate the knockout bracket tree for the 2026 FIFA World Cup.

Defines the complete advancement structure from R32 through R16, QF, SF,
3rd-place match, and Final.  Verifies and enforces ``next_match_id``
chains and ``position`` numbers for all 32 knockout-stage matches.

Supports idempotent execution -- re-running will verify and correct any
drift in the bracket linkage without duplicating data.

Usage::

    cd football-server
    python -m scripts.generate_bracket
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)

# ── Bracket linkage: (source_ext_id, target_ext_id, position) ────────────────
#
# ``position``: 1 = home slot, 2 = away slot in the target match.
# This models the **winner** path only.  The 3rd-place match (3RD_01)
# receives the SF losers by convention -- not encoded in ``next_match_id``
# because the SF matches already point to the Final.

BRACKET_LINKS: list[tuple[str, str, int]] = [
    # R32 -> R16
    ("R32_01", "R16_01", 1), ("R32_02", "R16_01", 2),
    ("R32_03", "R16_02", 1), ("R32_04", "R16_02", 2),
    ("R32_05", "R16_03", 1), ("R32_06", "R16_03", 2),
    ("R32_07", "R16_04", 1), ("R32_08", "R16_04", 2),
    ("R32_09", "R16_05", 1), ("R32_10", "R16_05", 2),
    ("R32_11", "R16_06", 1), ("R32_12", "R16_06", 2),
    ("R32_13", "R16_07", 1), ("R32_14", "R16_07", 2),
    ("R32_15", "R16_08", 1), ("R32_16", "R16_08", 2),
    # R16 -> QF
    ("R16_01", "QF_01", 1), ("R16_02", "QF_01", 2),
    ("R16_03", "QF_02", 1), ("R16_04", "QF_02", 2),
    ("R16_05", "QF_03", 1), ("R16_06", "QF_03", 2),
    ("R16_07", "QF_04", 1), ("R16_08", "QF_04", 2),
    # QF -> SF
    ("QF_01", "SF_01", 1), ("QF_02", "SF_01", 2),
    ("QF_03", "SF_02", 1), ("QF_04", "SF_02", 2),
    # SF -> Final
    ("SF_01", "F_01", 1), ("SF_02", "F_01", 2),
]

# ── 3rd-place match convention ────────────────────────────────────────────────
# SF losers feed into the 3rd-place match.  NOT encoded in ``next_match_id``
# because SF matches already point to the Final.  The bracket service
# handles this by convention (the "3rd" stage is a single standalone match).

THIRD_PLACE_MATCH: str = "3RD_01"

# ── R32 group qualification mapping ──────────────────────────────────────────
# Maps each R32 match to the group positions that feed into it.
# Format: {ext_id: (home_group, home_pos, away_group, away_pos)}
# pos: 1 = 1st place, 2 = 2nd place, 3 = 3rd place (best third-placed)
#
# 12 groups of 4 teams = 48.  Top 2 from each group (24 teams) + 8 best
# third-placed teams = 32 teams in R32.
#
# NOTE: Convention-based pairing.  Update with official FIFA draw when
# available.

R32_QUALIFICATION: dict[str, tuple[str, int, str, int]] = {
    "R32_01": ("A", 1, "B", 2),
    "R32_02": ("C", 1, "D", 2),
    "R32_03": ("E", 1, "F", 2),
    "R32_04": ("G", 1, "H", 2),
    "R32_05": ("I", 1, "J", 2),
    "R32_06": ("K", 1, "L", 2),
    "R32_07": ("B", 1, "A", 2),
    "R32_08": ("D", 1, "C", 2),
    "R32_09": ("F", 1, "E", 2),
    "R32_10": ("H", 1, "G", 2),
    "R32_11": ("J", 1, "I", 2),
    "R32_12": ("L", 1, "K", 2),
    "R32_13": ("C", 3, "F", 3),
    "R32_14": ("E", 3, "H", 3),
    "R32_15": ("A", 3, "D", 3),
    "R32_16": ("B", 3, "G", 3),
}

# ── Stage display names ──────────────────────────────────────────────────────

STAGE_ORDER: list[str] = ["R32", "R16", "QF", "SF", "3rd", "F"]

STAGE_MATCH_COUNT: dict[str, int] = {
    "R32": 16,
    "R16": 8,
    "QF": 4,
    "SF": 2,
    "3rd": 1,
    "F": 1,
}


# ── Core function ────────────────────────────────────────────────────────────


async def generate_bracket(session: AsyncSession) -> dict[str, Any]:
    """Verify and enforce the complete knockout bracket linkage.

    Returns a summary dict with counts of verified, corrected, and
    total links, plus the number of knockout matches found.
    """
    from app.models.match import Match

    stmt = select(Match).where(Match.stage.in_(STAGE_ORDER))
    result = await session.execute(stmt)
    matches: dict[str, Match] = {
        m.external_id: m for m in result.unique().scalars().all()
    }

    expected = sum(STAGE_MATCH_COUNT.values())  # 32
    if len(matches) < expected:
        logger.warning(
            "Only %d of %d knockout matches found. Run seed_matches first.",
            len(matches),
            expected,
        )

    verified = 0
    corrected = 0
    missing = 0

    for src_ext, tgt_ext, pos in BRACKET_LINKS:
        src = matches.get(src_ext)
        tgt = matches.get(tgt_ext)

        if src is None or tgt is None:
            missing += 1
            logger.warning(
                "Bracket link skip: %s -> %s (match not found)",
                src_ext,
                tgt_ext,
            )
            continue

        if src.next_match_id == tgt.id and src.position == pos:
            verified += 1
        else:
            src.next_match_id = tgt.id
            src.position = pos
            corrected += 1
            logger.debug("Corrected link: %s -> %s (pos=%d)", src_ext, tgt_ext, pos)

    await session.flush()

    # ── Per-stage summary ─────────────────────────────────────────────────
    stage_summary: dict[str, int] = {}
    for stage in STAGE_ORDER:
        stage_summary[stage] = sum(
            1 for m in matches.values() if m.stage == stage
        )

    logger.info(
        "Bracket linkage: verified=%d, corrected=%d, missing=%d, total=%d",
        verified,
        corrected,
        missing,
        len(BRACKET_LINKS),
    )

    return {
        "verified": verified,
        "corrected": corrected,
        "missing": missing,
        "total_links": len(BRACKET_LINKS),
        "total_matches": len(matches),
        "stage_summary": stage_summary,
        "third_place_exists": THIRD_PLACE_MATCH in matches,
    }


# ── CLI entry point ──────────────────────────────────────────────────────────


async def run() -> None:
    """Create an async session, run bracket generation, and print a summary."""
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
            result = await generate_bracket(session)

    await engine.dispose()

    stages = ", ".join(
        f"{k}={v}" for k, v in result["stage_summary"].items()
    )
    logger.info(
        "Bracket generation complete: %d matches [%s], "
        "%d links verified, %d corrected",
        result["total_matches"],
        stages,
        result["verified"],
        result["corrected"],
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
