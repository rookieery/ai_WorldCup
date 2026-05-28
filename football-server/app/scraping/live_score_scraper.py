"""Live score scraper — retrieves real-time match data from FIFA live scores page.

Inherits from :class:`BaseScraper` to leverage rate limiting, retry with
exponential backoff, and structured logging.

The scraper targets the FIFA live scores endpoint which returns current
match data.  Like :class:`FIFAScraper`, it first attempts to extract the
``__NEXT_DATA__`` JSON blob from the HTML response.  If that fails it
falls back to best-effort HTML parsing.

Data is validated through :class:`ScrapedLiveScoreBatch` before being
returned to the caller.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.config import settings
from app.schemas.scraper_schema import (
    ScrapedLiveEvent,
    ScrapedLiveScore,
    ScrapedLiveScoreBatch,
)

from .base_scraper import BaseScraper, ScraperParseError
from .fifa_scraper import _extract_next_data

logger = logging.getLogger(__name__)

# ── Activity level estimation ───────────────────────────────────────────────

_ACTIVITY_WEIGHTS: Dict[str, int] = {
    "goal": 25,
    "penalty": 20,
    "own_goal": 20,
    "red_card": 15,
    "yellow_card": 5,
    "substitution": 3,
    "var": 10,
}


def _estimate_activity_level(
    events: List[ScrapedLiveEvent],
    current_minute: int,
) -> int:
    """Estimate a 0-100 activity level based on recent events and match minute.

    The heuristic weighs recent events (last 10 minutes) more heavily and
    adds a baseline proportional to how far the match has progressed.
    """
    if current_minute <= 0:
        return 0

    base_activity = min(30, current_minute // 3)

    recent_event_score = 0
    for ev in events:
        age = current_minute - ev.minute
        if age < 0:
            continue
        weight = _ACTIVITY_WEIGHTS.get(ev.event_type, 2)
        recency_factor = max(0.1, 1.0 - age / 10.0) if age <= 10 else 0.1
        recent_event_score += int(weight * recency_factor)

    return min(100, base_activity + recent_event_score)


# ── LiveScoreScraper ────────────────────────────────────────────────────────


class LiveScoreScraper(BaseScraper):
    """Scraper for real-time FIFA World Cup 2026 live scores.

    Provides a high-level method to scrape all currently live matches
    with their real-time scores, events, and activity levels.  All
    methods return Pydantic-validated models.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._schedule_url = settings.FIFA_SCHEDULE_URL
        self._match_url_base = settings.FIFA_MATCH_URL

    # ── Public API ─────────────────────────────────────────────────────

    async def scrape_live_scores(self) -> ScrapedLiveScoreBatch:
        """Scrape real-time data for all currently live matches.

        Fetches the FIFA schedule page, extracts embedded JSON data,
        filters for matches with ``status == "live"``, and returns
        validated :class:`ScrapedLiveScoreBatch`.

        If no live matches are found, returns an empty batch.

        Raises
        ------
        ScraperHTTPError / ScraperTimeoutError
            Propagated from :class:`BaseScraper.fetch`.
        """
        html = await self.fetch(self._schedule_url)
        logger.info("Parsing live scores from %s", self._schedule_url)

        try:
            next_data = _extract_next_data(html, self._schedule_url)
        except ScraperParseError:
            logger.warning(
                "Could not extract __NEXT_DATA__ from schedule page; "
                "returning empty live scores"
            )
            return ScrapedLiveScoreBatch(
                matches=[],
                source_url=self._schedule_url,
            )

        live_scores = self._parse_live_scores(next_data)
        logger.info("Scraped %d live matches", len(live_scores))

        return ScrapedLiveScoreBatch(
            matches=live_scores,
            source_url=self._schedule_url,
        )

    # ── Live score parsing ─────────────────────────────────────────────

    def _parse_live_scores(
        self, next_data: Dict[str, Any]
    ) -> List[ScrapedLiveScore]:
        """Extract live match data from the page JSON payload."""
        matches_data = _find_matches_in_data(next_data)
        if matches_data is None:
            logger.warning("Could not locate match data in schedule page JSON")
            return []

        results: List[ScrapedLiveScore] = []
        for entry in matches_data:
            status = str(entry.get("status", "")).lower()
            if status not in ("live", "in_play", "inplay", "halftime", "1h", "2h", "et", "ht"):
                continue
            try:
                live_score = self._parse_single_live_score(entry)
                results.append(live_score)
            except Exception:
                logger.warning(
                    "Failed to parse live score entry: %s",
                    str(entry)[:200],
                    exc_info=True,
                )
        return results

    def _parse_single_live_score(
        self, entry: Dict[str, Any]
    ) -> ScrapedLiveScore:
        """Parse one match dict into a ScrapedLiveScore."""
        events = self._parse_live_events(entry)
        current_minute = self._extract_current_minute(entry)
        activity = _estimate_activity_level(events, current_minute)

        return ScrapedLiveScore(
            match_id=str(
                entry.get("matchId")
                or entry.get("id")
                or entry.get("externalId", "")
            ),
            home_score=int(entry.get("homeScore", 0)),
            away_score=int(entry.get("awayScore", 0)),
            status="live",
            activity_level=activity,
            events=events,
        )

    def _parse_live_events(
        self, entry: Dict[str, Any]
    ) -> List[ScrapedLiveEvent]:
        """Parse events from a live match entry."""
        raw_events = entry.get("events", [])
        if not isinstance(raw_events, list):
            return []

        results: List[ScrapedLiveEvent] = []
        for ev in raw_events:
            if not isinstance(ev, dict):
                continue
            try:
                results.append(
                    ScrapedLiveEvent(
                        event_type=str(
                            ev.get("type") or ev.get("eventType", "unknown")
                        ).lower(),
                        minute=int(ev.get("minute", 0)),
                        team_side=str(
                            ev.get("teamSide") or ev.get("side", "home")
                        ).lower(),
                        player_name=ev.get("playerName") or ev.get("player"),
                    )
                )
            except Exception:
                logger.warning(
                    "Failed to parse live event: %s",
                    str(ev)[:200],
                    exc_info=True,
                )
        return results

    @staticmethod
    def _extract_current_minute(entry: Dict[str, Any]) -> int:
        """Extract the current match minute from the entry data."""
        minute = entry.get("currentMinute") or entry.get("minute", 0)
        try:
            return max(0, int(minute))
        except (ValueError, TypeError):
            return 0


# ── JSON path helper ────────────────────────────────────────────────────────


def _find_matches_in_data(
    data: Dict[str, Any],
) -> Optional[List[Dict[str, Any]]]:
    """Walk the Next.js data tree to find the match list.

    Tries several known paths used by FIFA.com:
    - props.pageProps.matches
    - props.pageProps.liveMatches
    - props.pageProps.matchSchedule
    - props.pageProps.data.matches
    """
    props = data.get("props", {}).get("pageProps", {})
    if isinstance(props, dict):
        for key in ("liveMatches", "matches", "matchSchedule", "allMatches"):
            found = props.get(key)
            if isinstance(found, list):
                return found

        inner = props.get("data")
        if isinstance(inner, dict):
            for key in ("liveMatches", "matches", "matchSchedule"):
                found = inner.get(key)
                if isinstance(found, list):
                    return found

    return None
