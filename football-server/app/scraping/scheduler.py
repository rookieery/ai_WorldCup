"""Background scraper scheduler — periodic tasks orchestrated via asyncio.

Runs three periodic tasks at different intervals:

* **Live scores** (every 30 s) — scrapes live match data and syncs to Redis
  via :class:`DataSyncService`.  Skipped when no matches are currently live.
* **Finished results** (every 5 min) — scrapes recently finished matches and
  persists scores and events to SQLite.
* **Group standings** (every 1 h) — recalculates group standings from the
  latest match results.

The scheduler is designed to be started as an ``asyncio.Task`` from the
FastAPI lifespan.  Call :meth:`ScraperScheduler.start` to launch all
periodic loops and :meth:`ScraperScheduler.stop` to cancel and await them.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.scraping.data_sync import DataSyncService
from app.scraping.fifa_scraper import FIFAScraper
from app.scraping.live_score_scraper import LiveScoreScraper
from app.services.live_service import LiveService

logger = logging.getLogger(__name__)

# ── Delay between individual match result scrapes ───────────────────────────

_RESULT_SCRAPE_DELAY = 2


class ScraperScheduler:
    """Orchestrate periodic scraping tasks.

    Parameters
    ----------
    session_factory:
        An ``AsyncSession`` factory (from ``sessionmaker``) used to create
        per-task database sessions.
    redis:
        An optional ``redis.asyncio.Redis`` instance for distributed locking
        and live-data pushes.
    """

    def __init__(
        self,
        session_factory: sessionmaker,  # type: ignore[type-arg]
        redis: Optional[Redis] = None,
    ) -> None:
        self._session_factory = session_factory
        self._redis = redis
        self._tasks: list[asyncio.Task[None]] = []
        self._running = False

    # ── Lifecycle ───────────────────────────────────────────────────────────

    async def start(self) -> None:
        """Start all periodic scraper tasks.

        Safe to call when ``SCRAPER_ENABLED`` is ``False`` — the method
        returns immediately after logging a notice.
        """
        if not settings.SCRAPER_ENABLED:
            logger.info("Scraper scheduler disabled (SCRAPER_ENABLED=false)")
            return

        self._running = True
        logger.info("Starting scraper scheduler")

        self._tasks = [
            asyncio.create_task(
                self._run_periodically(
                    "live_scores",
                    self._sync_live_scores,
                    settings.SCRAPER_LIVE_INTERVAL,
                ),
                name="scraper-live-scores",
            ),
            asyncio.create_task(
                self._run_periodically(
                    "finished_results",
                    self._sync_finished_results,
                    settings.SCRAPER_FINISHED_INTERVAL,
                ),
                name="scraper-finished-results",
            ),
            asyncio.create_task(
                self._run_periodically(
                    "group_standings",
                    self._sync_group_standings,
                    settings.SCRAPER_GROUP_INTERVAL,
                ),
                name="scraper-group-standings",
            ),
        ]

    async def stop(self) -> None:
        """Cancel all running tasks and wait for them to finish."""
        if not self._tasks:
            return

        self._running = False
        logger.info("Stopping scraper scheduler — cancelling %d tasks", len(self._tasks))

        for task in self._tasks:
            task.cancel()

        results = await asyncio.gather(*self._tasks, return_exceptions=True)
        for task, result in zip(self._tasks, results):
            if isinstance(result, Exception) and not isinstance(result, asyncio.CancelledError):
                logger.warning(
                    "Scraper task %s raised: %s",
                    task.get_name(),
                    result,
                )

        self._tasks.clear()
        logger.info("Scraper scheduler stopped")

    # ── Periodic loop runner ────────────────────────────────────────────────

    async def _run_periodically(
        self,
        name: str,
        coro_fn: object,
        interval_seconds: int,
    ) -> None:
        """Run *coro_fn* every *interval_seconds*, logging errors but never stopping."""
        logger.info("Periodic task [%s] started (interval=%ds)", name, interval_seconds)
        while self._running:
            try:
                await coro_fn()  # type: ignore[misc]
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.error(
                    "Periodic task [%s] failed — will retry in %ds",
                    name,
                    interval_seconds,
                    exc_info=True,
                )
            await asyncio.sleep(interval_seconds)
        logger.info("Periodic task [%s] exiting", name)

    # ── Task implementations ───────────────────────────────────────────────

    async def _sync_live_scores(self) -> None:
        """Scrape live scores and push updates via DataSyncService."""
        live_service = LiveService(redis=self._redis)
        live_matches = await live_service.get_live_matches()

        if not live_matches:
            logger.debug("sync_live_scores: no live matches — skipping")
            return

        async with LiveScoreScraper() as scraper:
            batch = await scraper.scrape_live_scores()

        async with self._session_factory() as session:
            sync = DataSyncService(redis=self._redis, session=session)
            synced = await sync.sync_live_scores(batch)
            await session.commit()

        logger.info("sync_live_scores: %d matches synced", synced)

    async def _sync_finished_results(self) -> None:
        """Scrape results for recently finished matches and persist to DB."""
        async with self._session_factory() as session:
            from app.repositories.match_repo import MatchRepository

            match_repo = MatchRepository(session)
            finished_matches = await match_repo.get_by_status(
                "finished", page=1, page_size=10,
            )
            recent = finished_matches[0]

            if not recent:
                logger.debug("sync_finished_results: no recent finished matches")
                return

            async with FIFAScraper() as scraper:
                for match in recent:
                    if match.external_id and match.external_id.isdigit():
                        try:
                            result = await scraper.scrape_match_result(
                                int(match.external_id),
                            )
                            sync = DataSyncService(
                                redis=self._redis, session=session,
                            )
                            await sync.sync_match_result(result)
                        except Exception:
                            logger.warning(
                                "Failed to scrape result for match ext_id=%s",
                                match.external_id,
                                exc_info=True,
                            )
                    await asyncio.sleep(_RESULT_SCRAPE_DELAY)

            await session.commit()
            logger.info(
                "sync_finished_results: processed %d matches",
                len(recent),
            )

    async def _sync_group_standings(self) -> None:
        """Recalculate group standings from current match results."""
        async with self._session_factory() as session:
            sync = DataSyncService(redis=self._redis, session=session)
            updated = await sync.sync_group_standings()
            await session.commit()

        logger.info("sync_group_standings: %d rows updated", updated)
