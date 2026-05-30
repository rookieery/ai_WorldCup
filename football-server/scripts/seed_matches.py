"""Seed script: insert all 104 matches (72 group stage + 32 knockout) for the
2026 FIFA World Cup.

Supports idempotent execution -- existing matches (matched by ``external_id``)
are updated in-place rather than causing duplicate-key errors.

Usage::

    cd football-server
    python -m scripts.seed_matches
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from datetime import date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.utils.markdown_parser import MarkdownParser

logger = logging.getLogger(__name__)

# ── Real FIFA 2026 group-stage schedule ───────────────────────────────────────
# Keyed by external_id, value is (kickoff_utc, venue_name).
# Source: FIFA official schedule + Roadtrips.com (EST→UTC via EDT UTC-4).
_GROUP_MATCH_DATA: dict[str, tuple[datetime, str]] = {
    # Group A
    "A_M1": (datetime(2026, 6, 11, 19, 0), "Estadio Azteca"),          # Mexico vs South Africa  13:00 local
    "A_M2": (datetime(2026, 6, 12, 2, 0),  "Estadio Akron"),           # South Korea vs Czechia  20:00 local
    "A_M3": (datetime(2026, 6, 19, 1, 0),  "Estadio Akron"),           # Mexico vs South Korea   19:00 local
    "A_M4": (datetime(2026, 6, 18, 16, 0), "Mercedes-Benz Stadium"),   # Czechia vs South Africa 12:00 local
    "A_M5": (datetime(2026, 6, 25, 1, 0),  "Estadio Azteca"),          # Czechia vs Mexico       19:00 local
    "A_M6": (datetime(2026, 6, 25, 1, 0),  "Estadio BBVA"),            # South Africa vs Korea   19:00 local
    # Group B
    "B_M1": (datetime(2026, 6, 12, 19, 0), "BMO Field"),               # Canada vs Bosnia        15:00 local
    "B_M2": (datetime(2026, 6, 13, 19, 0), "Levi's Stadium"),          # Qatar vs Switzerland    12:00 local
    "B_M3": (datetime(2026, 6, 18, 22, 0), "BC Place"),                # Canada vs Qatar         15:00 local
    "B_M4": (datetime(2026, 6, 18, 19, 0), "SoFi Stadium"),            # Switzerland vs Bosnia   12:00 local
    "B_M5": (datetime(2026, 6, 24, 19, 0), "BC Place"),                # Switzerland vs Canada   12:00 local
    "B_M6": (datetime(2026, 6, 24, 19, 0), "Lumen Field"),             # Bosnia vs Qatar         12:00 local
    # Group C
    "C_M1": (datetime(2026, 6, 13, 22, 0), "MetLife Stadium"),         # Brazil vs Morocco       18:00 local
    "C_M2": (datetime(2026, 6, 14, 1, 0),  "Gillette Stadium"),        # Haiti vs Scotland       21:00 local
    "C_M3": (datetime(2026, 6, 20, 1, 0),  "Lincoln Financial Field"), # Brazil vs Haiti         21:00 local
    "C_M4": (datetime(2026, 6, 19, 22, 0), "Gillette Stadium"),        # Scotland vs Morocco     18:00 local
    "C_M5": (datetime(2026, 6, 24, 22, 0), "Hard Rock Stadium"),       # Scotland vs Brazil      18:00 local
    "C_M6": (datetime(2026, 6, 24, 22, 0), "Mercedes-Benz Stadium"),   # Morocco vs Haiti        18:00 local
    # Group D
    "D_M1": (datetime(2026, 6, 13, 1, 0),  "SoFi Stadium"),            # USA vs Paraguay         18:00 local
    "D_M2": (datetime(2026, 6, 13, 4, 0),  "BC Place"),                # Australia vs Türkiye    21:00 local
    "D_M3": (datetime(2026, 6, 19, 19, 0), "Lumen Field"),             # USA vs Australia        12:00 local
    "D_M4": (datetime(2026, 6, 20, 3, 0),  "Levi's Stadium"),          # Türkiye vs Paraguay     20:00 local
    "D_M5": (datetime(2026, 6, 26, 2, 0),  "SoFi Stadium"),            # Türkiye vs USA          19:00 local
    "D_M6": (datetime(2026, 6, 26, 2, 0),  "Levi's Stadium"),          # Paraguay vs Australia   19:00 local
    # Group E
    "E_M1": (datetime(2026, 6, 14, 17, 0), "NRG Stadium"),             # Germany vs Curaçao      12:00 local
    "E_M2": (datetime(2026, 6, 14, 23, 0), "Lincoln Financial Field"), # Ivory Coast vs Ecuador  19:00 local
    "E_M3": (datetime(2026, 6, 20, 20, 0), "BMO Field"),               # Germany vs Ivory Coast  16:00 local
    "E_M4": (datetime(2026, 6, 21, 0, 0),  "Arrowhead Stadium"),       # Ecuador vs Curaçao      19:00 local
    "E_M5": (datetime(2026, 6, 25, 20, 0), "Lincoln Financial Field"), # Curaçao vs Ivory Coast  16:00 local
    "E_M6": (datetime(2026, 6, 25, 20, 0), "MetLife Stadium"),         # Ecuador vs Germany      16:00 local
    # Group F
    "F_M1": (datetime(2026, 6, 14, 20, 0), "AT&T Stadium"),            # Netherlands vs Japan    15:00 local
    "F_M2": (datetime(2026, 6, 15, 2, 0),  "Estadio BBVA"),            # Sweden vs Tunisia       20:00 local
    "F_M3": (datetime(2026, 6, 20, 17, 0), "NRG Stadium"),             # Netherlands vs Sweden   12:00 local
    "F_M4": (datetime(2026, 6, 21, 4, 0),  "Estadio BBVA"),            # Tunisia vs Japan        22:00 local
    "F_M5": (datetime(2026, 6, 25, 23, 0), "Arrowhead Stadium"),       # Tunisia vs Netherlands  18:00 local
    "F_M6": (datetime(2026, 6, 25, 23, 0), "AT&T Stadium"),            # Japan vs Sweden         18:00 local
    # Group G
    "G_M1": (datetime(2026, 6, 15, 19, 0), "Lumen Field"),             # Belgium vs Egypt        12:00 local
    "G_M2": (datetime(2026, 6, 16, 1, 0),  "SoFi Stadium"),            # Iran vs New Zealand     18:00 local
    "G_M3": (datetime(2026, 6, 21, 19, 0), "SoFi Stadium"),            # Belgium vs Iran         12:00 local
    "G_M4": (datetime(2026, 6, 22, 1, 0),  "BC Place"),                # New Zealand vs Egypt    18:00 local
    "G_M5": (datetime(2026, 6, 27, 3, 0),  "BC Place"),                # New Zealand vs Belgium  20:00 local
    "G_M6": (datetime(2026, 6, 27, 3, 0),  "Lumen Field"),             # Egypt vs Iran           20:00 local
    # Group H
    "H_M1": (datetime(2026, 6, 15, 16, 0), "Mercedes-Benz Stadium"),   # Spain vs Cape Verde     12:00 local
    "H_M2": (datetime(2026, 6, 15, 22, 0), "Hard Rock Stadium"),       # Saudi Arabia vs Uruguay 18:00 local
    "H_M3": (datetime(2026, 6, 21, 16, 0), "Mercedes-Benz Stadium"),   # Spain vs Saudi Arabia   12:00 local
    "H_M4": (datetime(2026, 6, 21, 22, 0), "Hard Rock Stadium"),       # Uruguay vs Cape Verde   18:00 local
    "H_M5": (datetime(2026, 6, 27, 0, 0),  "Estadio Akron"),           # Uruguay vs Spain        18:00 local
    "H_M6": (datetime(2026, 6, 27, 0, 0),  "NRG Stadium"),             # Cape Verde vs Saudi     19:00 local
    # Group I
    "I_M1": (datetime(2026, 6, 16, 19, 0), "MetLife Stadium"),         # France vs Senegal       15:00 local
    "I_M2": (datetime(2026, 6, 16, 22, 0), "Gillette Stadium"),        # Iraq vs Norway          18:00 local
    "I_M3": (datetime(2026, 6, 22, 21, 0), "Lincoln Financial Field"), # France vs Iraq          17:00 local
    "I_M4": (datetime(2026, 6, 23, 0, 0),  "MetLife Stadium"),         # Norway vs Senegal       20:00 local
    "I_M5": (datetime(2026, 6, 26, 19, 0), "Gillette Stadium"),        # Norway vs France        15:00 local
    "I_M6": (datetime(2026, 6, 26, 19, 0), "BMO Field"),               # Senegal vs Iraq         15:00 local
    # Group J
    "J_M1": (datetime(2026, 6, 17, 1, 0),  "Arrowhead Stadium"),       # Argentina vs Algeria    20:00 local
    "J_M2": (datetime(2026, 6, 17, 4, 0),  "Levi's Stadium"),          # Austria vs Jordan       21:00 local
    "J_M3": (datetime(2026, 6, 22, 17, 0), "AT&T Stadium"),            # Argentina vs Austria    12:00 local
    "J_M4": (datetime(2026, 6, 23, 3, 0),  "Levi's Stadium"),          # Jordan vs Algeria       20:00 local
    "J_M5": (datetime(2026, 6, 28, 2, 0),  "Arrowhead Stadium"),       # Algeria vs Austria      21:00 local
    "J_M6": (datetime(2026, 6, 28, 2, 0),  "AT&T Stadium"),            # Jordan vs Argentina     21:00 local
    # Group K
    "K_M1": (datetime(2026, 6, 17, 17, 0), "NRG Stadium"),             # Portugal vs Congo DR    12:00 local
    "K_M2": (datetime(2026, 6, 18, 2, 0),  "Estadio Azteca"),          # Uzbekistan vs Colombia  20:00 local
    "K_M3": (datetime(2026, 6, 23, 17, 0), "NRG Stadium"),             # Portugal vs Uzbekistan  12:00 local
    "K_M4": (datetime(2026, 6, 24, 2, 0),  "Estadio Akron"),           # Colombia vs Congo DR    20:00 local
    "K_M5": (datetime(2026, 6, 27, 23, 30),"Hard Rock Stadium"),       # Colombia vs Portugal    19:30 local
    "K_M6": (datetime(2026, 6, 27, 23, 30),"Mercedes-Benz Stadium"),   # Congo DR vs Uzbekistan  19:30 local
    # Group L
    "L_M1": (datetime(2026, 6, 17, 20, 0), "AT&T Stadium"),            # England vs Croatia      15:00 local
    "L_M2": (datetime(2026, 6, 17, 23, 0), "BMO Field"),               # Ghana vs Panama         19:00 local
    "L_M3": (datetime(2026, 6, 23, 20, 0), "Gillette Stadium"),        # England vs Ghana        16:00 local
    "L_M4": (datetime(2026, 6, 23, 23, 0), "BMO Field"),               # Panama vs Croatia       19:00 local
    "L_M5": (datetime(2026, 6, 27, 21, 0), "MetLife Stadium"),         # Panama vs England       17:00 local
    "L_M6": (datetime(2026, 6, 27, 21, 0), "Lincoln Financial Field"), # Croatia vs Ghana        17:00 local
}

# ── Knockout schedule definitions ──────────────────────────────────────────────

_KNOCKOUT_DEFS: list[dict[str, Any]] = [
    # Round of 32 — 16 matches (official FIFA 2026 schedule, UTC times)
    # R32_01=M73, R32_02=M76, R32_03=M74, R32_04=M75, R32_05=M78, R32_06=M77,
    # R32_07=M79, R32_08=M80, R32_09=M82, R32_10=M81, R32_11=M84, R32_12=M83,
    # R32_13=M85, R32_14=M88, R32_15=M86, R32_16=M87
    {"ext": "R32_01", "stage": "R32", "d": date(2026, 6, 28), "h": 19},   # M73 2Avs2B   Inglewood
    {"ext": "R32_02", "stage": "R32", "d": date(2026, 6, 29), "h": 17},   # M76 1Cvs2F   Houston
    {"ext": "R32_03", "stage": "R32", "d": date(2026, 6, 29), "h": 20},   # M74 1Evs3rd  Foxborough
    {"ext": "R32_04", "stage": "R32", "d": date(2026, 6, 30), "h": 1},    # M75 1Fvs2C   Guadalupe
    {"ext": "R32_05", "stage": "R32", "d": date(2026, 6, 30), "h": 17},   # M78 2Evs2I   Arlington
    {"ext": "R32_06", "stage": "R32", "d": date(2026, 6, 30), "h": 21},   # M77 1Ivs3rd  East Rutherford
    {"ext": "R32_07", "stage": "R32", "d": date(2026, 7, 1), "h": 1},     # M79 1Avs3rd  Mexico City
    {"ext": "R32_08", "stage": "R32", "d": date(2026, 7, 1), "h": 16},    # M80 1Lvs3rd  Atlanta
    {"ext": "R32_09", "stage": "R32", "d": date(2026, 7, 1), "h": 20},    # M82 1Gvs3rd  Seattle
    {"ext": "R32_10", "stage": "R32", "d": date(2026, 7, 2), "h": 0},     # M81 1Dvs3rd  Santa Clara
    {"ext": "R32_11", "stage": "R32", "d": date(2026, 7, 2), "h": 19},    # M84 1Hvs2J   Inglewood
    {"ext": "R32_12", "stage": "R32", "d": date(2026, 7, 2), "h": 23},    # M83 2Kvs2L   Toronto
    {"ext": "R32_13", "stage": "R32", "d": date(2026, 7, 3), "h": 3},     # M85 1Bvs3rd  Vancouver
    {"ext": "R32_14", "stage": "R32", "d": date(2026, 7, 3), "h": 18},    # M88 2Dvs2G   Arlington
    {"ext": "R32_15", "stage": "R32", "d": date(2026, 7, 3), "h": 22},    # M86 1Jvs2H   Miami Gardens
    {"ext": "R32_16", "stage": "R32", "d": date(2026, 7, 4), "h": 1},     # M87 1Kvs3rd  Kansas City
    # Round of 16 — 8 matches (official FIFA schedule)
    {"ext": "R16_01", "stage": "R16", "d": date(2026, 7, 4), "h": 21},    # M89 Philadelphia
    {"ext": "R16_02", "stage": "R16", "d": date(2026, 7, 4), "h": 17},    # M90 Houston
    {"ext": "R16_03", "stage": "R16", "d": date(2026, 7, 5), "h": 20},    # M91 East Rutherford
    {"ext": "R16_04", "stage": "R16", "d": date(2026, 7, 6), "h": 0},     # M92 Mexico City
    {"ext": "R16_05", "stage": "R16", "d": date(2026, 7, 6), "h": 19},    # M93 Arlington
    {"ext": "R16_06", "stage": "R16", "d": date(2026, 7, 7), "h": 0},     # M94 Seattle
    {"ext": "R16_07", "stage": "R16", "d": date(2026, 7, 7), "h": 16},    # M95 Atlanta
    {"ext": "R16_08", "stage": "R16", "d": date(2026, 7, 7), "h": 20},    # M96 Vancouver
    # Quarter-finals (official: Jul 9-11)
    {"ext": "QF_01", "stage": "QF", "d": date(2026, 7, 9), "h": 20},      # M97 Foxborough
    {"ext": "QF_02", "stage": "QF", "d": date(2026, 7, 10), "h": 19},     # M98 Inglewood
    {"ext": "QF_03", "stage": "QF", "d": date(2026, 7, 11), "h": 21},     # M99 Miami Gardens
    {"ext": "QF_04", "stage": "QF", "d": date(2026, 7, 12), "h": 1},      # M100 Kansas City
    # Semi-finals
    {"ext": "SF_01", "stage": "SF", "d": date(2026, 7, 14), "h": 19},     # M101 Arlington
    {"ext": "SF_02", "stage": "SF", "d": date(2026, 7, 15), "h": 19},     # M102 Atlanta
    # Third-place match
    {"ext": "3RD_01", "stage": "3rd", "d": date(2026, 7, 18), "h": 21},   # M103 Miami Gardens
    # Final
    {"ext": "F_01", "stage": "F", "d": date(2026, 7, 19), "h": 19},       # M104 East Rutherford
]

_ROUND_NAMES: dict[str, str] = {
    "R32": "Round of 32",
    "R16": "Round of 16",
    "QF": "Quarter-finals",
    "SF": "Semi-finals",
    "3rd": "Third-place match",
    "F": "Final",
}

# Venue overrides for knockout matches (keyed by external_id).
# Official FIFA 2026 venues.
_VENUE_OVERRIDES: dict[str, str] = {
    # R32 venues (official FIFA schedule)
    "R32_01": "SoFi Stadium",             # M73: Inglewood
    "R32_02": "NRG Stadium",              # M76: Houston
    "R32_03": "Gillette Stadium",         # M74: Foxborough
    "R32_04": "Estadio BBVA",             # M75: Guadalupe
    "R32_05": "AT&T Stadium",             # M78: Arlington
    "R32_06": "MetLife Stadium",          # M77: East Rutherford
    "R32_07": "Estadio Azteca",           # M79: Mexico City
    "R32_08": "Mercedes-Benz Stadium",    # M80: Atlanta
    "R32_09": "Lumen Field",             # M82: Seattle
    "R32_10": "Levi's Stadium",           # M81: Santa Clara
    "R32_11": "SoFi Stadium",             # M84: Inglewood
    "R32_12": "BMO Field",               # M83: Toronto
    "R32_13": "BC Place",                 # M85: Vancouver
    "R32_14": "AT&T Stadium",             # M88: Arlington
    "R32_15": "Hard Rock Stadium",        # M86: Miami Gardens
    "R32_16": "Arrowhead Stadium",        # M87: Kansas City
    # R16 venues
    "R16_01": "Lincoln Financial Field",  # M89: Philadelphia
    "R16_02": "NRG Stadium",              # M90: Houston
    "R16_03": "MetLife Stadium",          # M91: East Rutherford
    "R16_04": "Estadio Azteca",           # M92: Mexico City
    "R16_05": "AT&T Stadium",             # M93: Arlington
    "R16_06": "Lumen Field",              # M94: Seattle
    "R16_07": "Mercedes-Benz Stadium",    # M95: Atlanta
    "R16_08": "BC Place",                 # M96: Vancouver
    # QF venues
    "QF_01": "Gillette Stadium",          # M97: Foxborough
    "QF_02": "SoFi Stadium",              # M98: Inglewood
    "QF_03": "Hard Rock Stadium",         # M99: Miami Gardens
    "QF_04": "Arrowhead Stadium",         # M100: Kansas City
    # SF venues
    "SF_01": "AT&T Stadium",              # M101: Arlington
    "SF_02": "Mercedes-Benz Stadium",     # M102: Atlanta
    # 3rd & Final
    "3RD_01": "Hard Rock Stadium",        # M103: Miami Gardens
    "F_01": "MetLife Stadium",            # M104: East Rutherford
}

# ── Bracket linkage: (source_ext_id, target_ext_id, position) ─────────────────

_BRACKET_LINKS: list[tuple[str, str, int]] = [
    # R32 -> R16  (official FIFA 2026 bracket)
    ("R32_03", "R16_01", 1), ("R32_06", "R16_01", 2),  # M74→M89, M77→M89
    ("R32_01", "R16_02", 1), ("R32_04", "R16_02", 2),  # M73→M90, M75→M90
    ("R32_02", "R16_03", 1), ("R32_05", "R16_03", 2),  # M76→M91, M78→M91
    ("R32_07", "R16_04", 1), ("R32_08", "R16_04", 2),  # M79→M92, M80→M92
    ("R32_12", "R16_05", 1), ("R32_11", "R16_05", 2),  # M83→M93, M84→M93
    ("R32_10", "R16_06", 1), ("R32_09", "R16_06", 2),  # M81→M94, M82→M94
    ("R32_15", "R16_07", 1), ("R32_14", "R16_07", 2),  # M86→M95, M88→M95
    ("R32_13", "R16_08", 1), ("R32_16", "R16_08", 2),  # M85→M96, M87→M96
    # R16 -> QF
    ("R16_01", "QF_01", 1), ("R16_02", "QF_01", 2),  # M89→M97, M90→M97
    ("R16_05", "QF_02", 1), ("R16_06", "QF_02", 2),  # M93→M98, M94→M98
    ("R16_03", "QF_03", 1), ("R16_04", "QF_03", 2),  # M91→M99, M92→M99
    ("R16_07", "QF_04", 1), ("R16_08", "QF_04", 2),  # M95→M100, M96→M100
    # QF -> SF
    ("QF_01", "SF_01", 1), ("QF_02", "SF_01", 2),  # M97→M101, M98→M101
    ("QF_03", "SF_02", 1), ("QF_04", "SF_02", 2),  # M99→M102, M100→M102
    # SF -> Final
    ("SF_01", "F_01", 1), ("SF_02", "F_01", 2),
]


# ── Helper functions ───────────────────────────────────────────────────────────


async def _ensure_tbd_team(session: AsyncSession) -> int:
    """Return the ID of the TBD placeholder team, creating it if absent."""
    from app.models.team import Team

    stmt = select(Team).where(Team.code == "TBD")
    result = await session.execute(stmt)
    team = result.unique().scalar_one_or_none()
    if team is not None:
        return team.id

    team = Team(
        name="TBD",
        name_zh="待定",
        code="TBD",
        flag="🏳️",
        fifa_ranking=0,
        group_label="X",
        confederation="",
        world_cup_appearances=0,
    )
    session.add(team)
    await session.flush()
    logger.info("Created TBD placeholder team (id=%d)", team.id)
    return team.id


async def _upsert_match(
    session: AsyncSession,
    ext_id: str,
    data: dict[str, Any],
    inserted: int,
    updated: int,
    skipped: int,
) -> tuple[int, int, int]:
    """Insert a new match or update an existing one matched by *ext_id*."""
    from app.models.match import Match

    stmt = select(Match).where(Match.external_id == ext_id)
    result = await session.execute(stmt)
    existing = result.unique().scalar_one_or_none()

    if existing is None:
        session.add(Match(**data))
        return inserted + 1, updated, skipped

    changed = False
    for key, value in data.items():
        if getattr(existing, key, None) != value:
            setattr(existing, key, value)
            changed = True
    if changed:
        return inserted, updated + 1, skipped
    return inserted, updated, skipped + 1


async def _link_bracket(session: AsyncSession) -> None:
    """Wire up next_match_id and position for knockout matches."""
    from app.models.match import Match

    stages = ["R32", "R16", "QF", "SF", "3rd", "F"]
    stmt = select(Match).where(Match.stage.in_(stages))
    result = await session.execute(stmt)
    matches = {m.external_id: m for m in result.unique().scalars().all()}

    for src_ext, tgt_ext, pos in _BRACKET_LINKS:
        src = matches.get(src_ext)
        tgt = matches.get(tgt_ext)
        if src is None or tgt is None:
            logger.warning("Bracket link skip: %s -> %s", src_ext, tgt_ext)
            continue
        src.next_match_id = tgt.id
        src.position = pos

    await session.flush()
    logger.info("Bracket linkage applied (%d links)", len(_BRACKET_LINKS))


# ── Main seed function ─────────────────────────────────────────────────────────


async def seed_matches(session: AsyncSession) -> dict[str, int]:
    """Insert or update all 104 matches (72 group + 32 knockout).

    Returns a summary dict with ``inserted``, ``updated``, ``skipped``,
    ``group_stage``, and ``knockout`` counts.
    """
    from app.models.team import Team
    from app.models.venue import Venue

    # ── Load reference data ─────────────────────────────────────────────
    result = await session.execute(select(Team))
    teams = result.unique().scalars().all()
    name_zh_to_id: dict[str, int] = {t.name_zh: t.id for t in teams}

    result = await session.execute(select(Venue).order_by(Venue.id))
    venues = list(result.unique().scalars().all())
    venue_by_name: dict[str, int] = {v.name: v.id for v in venues}

    tbd_id = await _ensure_tbd_team(session)

    # ── Parse group-stage fixtures ──────────────────────────────────────
    parser = MarkdownParser()
    parsed = parser.parse()
    if len(parsed) != 72:
        raise ValueError(f"Expected 72 group-stage matches, parsed {len(parsed)}")

    by_date: dict[date, list] = defaultdict(list)
    for pm in parsed:
        by_date[pm.match_date].append(pm)

    sorted_dates = sorted(by_date.keys())
    for d in sorted_dates:
        by_date[d].sort(key=lambda m: (m.group_label, m.round_num))

    # ── Insert group-stage matches ──────────────────────────────────────
    inserted, updated, skipped = 0, 0, 0
    venue_idx = 0
    group_counter: dict[str, int] = defaultdict(int)

    for d in sorted_dates:
        day_matches = by_date[d]

        for slot, pm in enumerate(day_matches):
            group_counter[pm.group_label] += 1
            ext_id = f"{pm.group_label}_M{group_counter[pm.group_label]}"

            home_id = name_zh_to_id.get(pm.home_team_zh)
            away_id = name_zh_to_id.get(pm.away_team_zh)
            if home_id is None:
                raise ValueError(f"Unknown home team: {pm.home_team_zh!r}")
            if away_id is None:
                raise ValueError(f"Unknown away team: {pm.away_team_zh!r}")

            match_info = _GROUP_MATCH_DATA.get(ext_id)
            if match_info:
                kickoff, venue_name = match_info
                vid = venue_by_name.get(venue_name, venues[0].id)
            else:
                vid = venues[venue_idx % len(venues)].id
                venue_idx += 1
                kickoff = datetime(
                    pm.match_date.year, pm.match_date.month,
                    pm.match_date.day, 18, 0,
                )

            data: dict[str, Any] = {
                "external_id": ext_id,
                "home_team_id": home_id,
                "away_team_id": away_id,
                "venue_id": vid,
                "stage": "group",
                "group_label": pm.group_label,
                "round": f"Matchday {pm.round_num}",
                "match_day": pm.round_num,
                "kickoff_utc": kickoff,
                "status": "upcoming",
                "home_score": None,
                "away_score": None,
                "is_big_match": False,
                "activity_level": 0,
                "next_match_id": None,
                "position": None,
            }
            inserted, updated, skipped = await _upsert_match(
                session, ext_id, data, inserted, updated, skipped,
            )

    await session.flush()
    logger.info(
        "Group stage: inserted=%d, updated=%d, skipped=%d",
        inserted, updated, skipped,
    )

    # ── Insert knockout matches ─────────────────────────────────────────
    ko_ins, ko_upd, ko_skip = 0, 0, 0
    ko_venue_idx = 0

    for kd in _KNOCKOUT_DEFS:
        override = _VENUE_OVERRIDES.get(kd["ext"])
        if override and override in venue_by_name:
            vid = venue_by_name[override]
        else:
            vid = venues[ko_venue_idx % len(venues)].id
            ko_venue_idx += 1

        kickoff = datetime(kd["d"].year, kd["d"].month, kd["d"].day, kd["h"], 0)
        stage = kd["stage"]

        data = {
            "external_id": kd["ext"],
            "home_team_id": tbd_id,
            "away_team_id": tbd_id,
            "venue_id": vid,
            "stage": stage,
            "group_label": None,
            "round": _ROUND_NAMES.get(stage, stage),
            "match_day": None,
            "kickoff_utc": kickoff,
            "status": "upcoming",
            "home_score": None,
            "away_score": None,
            "is_big_match": stage in ("QF", "SF", "3rd", "F"),
            "activity_level": 0,
            # next_match_id / position are managed by _link_bracket
        }
        ko_ins, ko_upd, ko_skip = await _upsert_match(
            session, kd["ext"], data, ko_ins, ko_upd, ko_skip,
        )

    await session.flush()
    logger.info(
        "Knockout: inserted=%d, updated=%d, skipped=%d",
        ko_ins, ko_upd, ko_skip,
    )

    # ── Bracket linkage ─────────────────────────────────────────────────
    await _link_bracket(session)

    return {
        "inserted": inserted + ko_ins,
        "updated": updated + ko_upd,
        "skipped": skipped + ko_skip,
        "group_stage": inserted + updated + skipped,
        "knockout": ko_ins + ko_upd + ko_skip,
    }


# ── CLI entry point ────────────────────────────────────────────────────────────


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
            result = await seed_matches(session)

    await engine.dispose()

    total = result["inserted"] + result["updated"] + result["skipped"]
    logger.info(
        "Seed complete: %d matches processed "
        "(group=%d, knockout=%d, inserted=%d, updated=%d, skipped=%d)",
        total,
        result["group_stage"],
        result["knockout"],
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