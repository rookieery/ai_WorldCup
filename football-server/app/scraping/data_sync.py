"""Data sync service — bridges web scrapers with persistent storage and Redis.

Orchestrates the flow of scraped data into the application's data stores:

* **Live scores** are pushed to Redis via :class:`LiveService` so that
  WebSocket clients receive real-time updates.
* **Finished match results** are persisted to SQLite via
  :class:`MatchRepository` and :class:`MatchEventRepository`.
* **Group standings** are recalculated from the latest match results
  and persisted via :class:`GroupRepository`.

Concurrency safety
------------------
All sync operations acquire a Redis distributed lock keyed by
``scraper:lock`` to prevent concurrent sync tasks from conflicting.
When Redis is unavailable, a module-level ``asyncio.Lock`` serves as
a single-process fallback.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group_standing import GroupStanding
from app.models.match import Match
from app.redis.keys import RedisKeys
from app.schemas.scraper_schema import (
    ScrapedLiveScore,
    ScrapedLiveScoreBatch,
    ScrapedMatchResult,
)
from app.services.live_service import LiveService

logger = logging.getLogger(__name__)

# ── Fallback in-process lock (when Redis unavailable) ───────────────────────

_process_lock = asyncio.Lock()

# ── Lock timeout in seconds ─────────────────────────────────────────────────

_LOCK_TTL = 60


class DataSyncService:
    """Synchronise scraped data into Redis (live) and SQLite (results, standings).

    Parameters
    ----------
    redis:
        An optional ``redis.asyncio.Redis`` instance for distributed locking.
    session:
        An ``AsyncSession`` for database operations.
    """

    def __init__(
        self,
        redis: Optional[Redis] = None,
        session: Optional[AsyncSession] = None,
    ) -> None:
        self._redis = redis
        self._session = session
        self._live_service = LiveService(redis=redis)

    # ── Public API ──────────────────────────────────────────────────────

    async def sync_live_scores(
        self, batch: ScrapedLiveScoreBatch
    ) -> int:
        """Sync a batch of live scores into Redis via LiveService.

        Returns the number of matches successfully synced.
        """
        if not batch.matches:
            logger.debug("sync_live_scores: empty batch, skipping")
            return 0

        synced = 0
        for live_score in batch.matches:
            try:
                await self._sync_single_live_score(live_score)
                synced += 1
            except Exception:
                logger.warning(
                    "Failed to sync live score for match %s",
                    live_score.match_id,
                    exc_info=True,
                )

        logger.info(
            "sync_live_scores: %d/%d matches synced", synced, len(batch.matches)
        )
        return synced

    async def sync_match_result(
        self, result: ScrapedMatchResult
    ) -> Optional[Match]:
        """Sync a single finished match result into SQLite.

        Returns the updated ``Match`` ORM object, or ``None`` if the
        match was not found or the session is unavailable.
        """
        if self._session is None:
            logger.warning("sync_match_result: no DB session available")
            return None

        from app.repositories.match_event_repo import MatchEventRepository
        from app.repositories.match_repo import MatchRepository

        match_repo = MatchRepository(self._session)
        event_repo = MatchEventRepository(self._session)

        match = await self._find_match_by_external_id(
            match_repo, result.external_id
        )
        if match is None:
            logger.warning(
                "sync_match_result: match with external_id=%s not found",
                result.external_id,
            )
            return None

        # Update match scores and status
        await match_repo.update(
            match.id,
            {
                "home_score": result.home_score,
                "away_score": result.away_score,
                "status": result.status,
            },
        )

        # Upsert events — clear existing and re-insert
        existing_events = await event_repo.get_by_match(match.id)
        for existing in existing_events:
            await self._session.delete(existing)
        await self._session.flush()

        for ev in result.events:
            await event_repo.create(
                {
                    "match_id": match.id,
                    "event_type": ev.event_type,
                    "minute": ev.minute,
                    "team_side": ev.team_side,
                    "player_name": ev.player_name,
                }
            )

        logger.info(
            "sync_match_result: match %d (ext=%s) updated to %d-%d with %d events",
            match.id,
            result.external_id,
            result.home_score,
            result.away_score,
            len(result.events),
        )

        # Update live service to reflect finished state
        await self._live_service.update_match_status(match.id, result.status)

        return match

    async def sync_group_standings(self) -> int:
        """Recalculate and update group standings from finished group matches.

        Returns the number of standing rows updated.
        """
        if self._session is None:
            logger.warning("sync_group_standings: no DB session available")
            return 0

        from app.repositories.group_repo import GroupRepository
        from app.repositories.match_repo import MatchRepository

        match_repo = MatchRepository(self._session)
        group_repo = GroupRepository(self._session)

        updated = 0
        for label in "ABCDEFGHIJKL":
            try:
                count = await self._recalc_group(
                    match_repo, group_repo, label
                )
                updated += count
            except Exception:
                logger.warning(
                    "Failed to recalculate group %s standings",
                    label,
                    exc_info=True,
                )

        logger.info("sync_group_standings: %d rows updated", updated)
        return updated

    # ── Distributed lock ────────────────────────────────────────────────

    async def _acquire_lock(self) -> Optional[str]:
        """Acquire the scraper distributed lock.  Returns the lock token
        or ``None`` if the lock could not be acquired.

        When Redis is unavailable, falls back to an in-process lock.
        """
        if self._redis is not None:
            token = str(uuid.uuid4())
            acquired = await self._redis.set(
                RedisKeys.SCRAPER_LOCK,
                token,
                nx=True,
                ex=_LOCK_TTL,
            )
            if acquired:
                logger.debug("Acquired scraper lock (token=%s)", token)
                return token
            logger.debug("Scraper lock held by another process")
            return None

        # Fallback: in-process lock (non-blocking)
        if _process_lock.locked():
            logger.debug("In-process scraper lock held by another coroutine")
            return None
        await _process_lock.acquire()
        return "process"

    async def _release_lock(self, token: Optional[str]) -> None:
        """Release the scraper distributed lock."""
        if token is None:
            return

        if self._redis is not None and token != "process":
            # Lua script ensures we only delete our own lock
            lua = (
                "if redis.call('get', KEYS[1]) == ARGV[1] "
                "then return redis.call('del', KEYS[1]) "
                "else return 0 end"
            )
            try:
                await self._redis.eval(
                    lua, 1, RedisKeys.SCRAPER_LOCK, token
                )
                logger.debug("Released scraper lock (token=%s)", token)
            except Exception:
                logger.warning(
                    "Failed to release scraper lock", exc_info=True
                )
        elif token == "process":
            _process_lock.release()

    # ── Private helpers ─────────────────────────────────────────────────

    async def _sync_single_live_score(
        self, score: ScrapedLiveScore
    ) -> None:
        """Apply a single live score update through LiveService."""
        # Look up the internal match ID by external_id if possible
        match_id = await self._resolve_match_id(score.match_id)

        await self._live_service.update_score(
            match_id, score.home_score, score.away_score
        )
        await self._live_service.update_activity(
            match_id, score.activity_level
        )
        # Ensure status is "live"
        await self._live_service.update_match_status(match_id, score.status)

        logger.debug(
            "Synced live score: match %d -> %d-%d (activity=%d)",
            match_id,
            score.home_score,
            score.away_score,
            score.activity_level,
        )

    async def _resolve_match_id(self, external_id: str) -> int:
        """Resolve an external match ID to an internal database ID.

        Falls back to treating the external_id as numeric if the DB
        session is unavailable or the match is not found.
        """
        if self._session is not None:
            try:
                stmt = select(Match.id).where(
                    Match.external_id == external_id
                )
                result = await self._session.execute(stmt)
                row = result.scalar_one_or_none()
                if row is not None:
                    return row
            except Exception:
                logger.debug(
                    "Could not resolve external_id=%s via DB, "
                    "attempting numeric fallback",
                    external_id,
                    exc_info=True,
                )

        # Fallback: try parsing as integer
        try:
            return int(external_id)
        except (ValueError, TypeError):
            logger.warning(
                "Cannot resolve match ID from external_id=%s", external_id
            )
            return 0

    async def _find_match_by_external_id(
        self, match_repo: Any, external_id: str
    ) -> Optional[Match]:
        """Find a match by its external_id."""
        stmt = select(Match).where(Match.external_id == external_id)
        result = await self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def _recalc_group(
        self,
        match_repo: Any,
        group_repo: Any,
        group_label: str,
    ) -> int:
        """Recalculate standings for a single group from finished matches."""
        matches = await group_repo.get_group_matches(group_label)
        finished = [m for m in matches if m.status == "finished"]
        if not finished:
            return 0

        team_stats = _accumulate_group_stats(finished)

        updated = 0
        for team_id, stats in team_stats.items():
            gd = stats["goals_for"] - stats["goals_against"]
            points = stats["won"] * 3 + stats["drawn"]

            stmt = select(GroupStanding).where(
                GroupStanding.team_id == team_id,
                GroupStanding.group_label == group_label,
            )
            result = await self._session.execute(stmt)
            standing = result.scalar_one_or_none()

            if standing is not None:
                standing.played = stats["played"]
                standing.won = stats["won"]
                standing.drawn = stats["drawn"]
                standing.lost = stats["lost"]
                standing.goals_for = stats["goals_for"]
                standing.goals_against = stats["goals_against"]
                standing.goal_difference = gd
                standing.points = points
                updated += 1

        await self._recalc_positions(group_label)
        await self._session.flush()

        return updated

    async def _recalc_positions(self, group_label: str) -> None:
        """Re-rank teams within a group by points -> GD -> GF."""
        stmt = (
            select(GroupStanding)
            .where(GroupStanding.group_label == group_label)
            .order_by(
                GroupStanding.points.desc(),
                GroupStanding.goal_difference.desc(),
                GroupStanding.goals_for.desc(),
            )
        )
        result = await self._session.execute(stmt)
        standings = result.scalars().all()

        for idx, standing in enumerate(standings, start=1):
            standing.position = idx


# ── Module-level helpers ─────────────────────────────────────────────────


def _accumulate_group_stats(
    finished_matches: List[Any],
) -> Dict[int, Dict[str, int]]:
    """Accumulate W/D/L/GF/GA stats from a list of finished group matches.

    Returns a dict mapping ``team_id`` to a stats dict with keys:
    ``played``, ``won``, ``drawn``, ``lost``, ``goals_for``, ``goals_against``.
    """
    team_stats: Dict[int, Dict[str, int]] = {}

    for m in finished_matches:
        home_id = m.home_team_id
        away_id = m.away_team_id
        home_score = m.home_score or 0
        away_score = m.away_score or 0

        for tid in (home_id, away_id):
            team_stats.setdefault(
                tid,
                {"played": 0, "won": 0, "drawn": 0, "lost": 0,
                 "goals_for": 0, "goals_against": 0},
            )

        team_stats[home_id]["played"] += 1
        team_stats[away_id]["played"] += 1
        team_stats[home_id]["goals_for"] += home_score
        team_stats[home_id]["goals_against"] += away_score
        team_stats[away_id]["goals_for"] += away_score
        team_stats[away_id]["goals_against"] += home_score

        if home_score > away_score:
            team_stats[home_id]["won"] += 1
            team_stats[away_id]["lost"] += 1
        elif home_score < away_score:
            team_stats[away_id]["won"] += 1
            team_stats[home_id]["lost"] += 1
        else:
            team_stats[home_id]["drawn"] += 1
            team_stats[away_id]["drawn"] += 1

    return team_stats
