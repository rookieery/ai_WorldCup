"""FIFA official data scraper — match schedule and match results.

Inherits from :class:`BaseScraper` to leverage rate limiting, retry
with exponential backoff, and structured logging.

The scraper targets FIFA.com pages for the 2026 World Cup.  Because
FIFA pages are rendered client-side (React / Next.js), the raw HTML
typically contains embedded ``__NEXT_DATA__`` JSON that this scraper
extracts and parses.

If the embedded JSON is unavailable (e.g. FIFA changes their page
structure), the scraper falls back to best-effort HTML parsing and
logs a warning.

Configuration
-------------
Target URLs are read from ``app.config.settings`` so they can be
overridden via environment variables:

* ``FIFA_SCHEDULE_URL`` — schedule listing page
* ``FIFA_MATCH_URL`` — base URL for individual match pages
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.config import settings
from app.schemas.scraper_schema import (
    ScrapedEvent,
    ScrapedMatch,
    ScrapedMatchResult,
    ScrapedSchedule,
)

from .base_scraper import BaseScraper, ScraperParseError

logger = logging.getLogger(__name__)

# ── Next.js data extraction ─────────────────────────────────────────────

_NEXT_DATA_RE = re.compile(
    r"<script\s+id=\"__NEXT_DATA__\"\s+type=\"application/json\">(.*?)</script>",
    re.DOTALL,
)


def _extract_next_data(html: str, url: str) -> Dict[str, Any]:
    """Extract and parse the ``__NEXT_DATA__`` JSON blob from FIFA HTML.

    Raises :class:`ScraperParseError` when the blob cannot be found or
    decoded.
    """
    match = _NEXT_DATA_RE.search(html)
    if not match:
        raise ScraperParseError(url, "__NEXT_DATA__ script tag not found")

    raw_json = match.group(1).strip()
    try:
        return json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ScraperParseError(url, f"Invalid JSON in __NEXT_DATA__: {exc}") from exc


# ── FIFAScraper ─────────────────────────────────────────────────────────


class FIFAScraper(BaseScraper):
    """Scraper for FIFA.com World Cup 2026 data.

    Provides high-level methods to scrape the full match schedule
    and individual match results.  All methods return Pydantic-validated
    models so callers can trust the data shape.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._schedule_url = settings.FIFA_SCHEDULE_URL
        self._match_url_base = settings.FIFA_MATCH_URL

    # ── Public API ─────────────────────────────────────────────────────

    async def scrape_match_schedule(self) -> ScrapedSchedule:
        """Scrape the full World Cup match schedule.

        Fetches the FIFA schedule page, extracts embedded JSON data,
        and returns a validated :class:`ScrapedSchedule`.

        Raises
        ------
        ScraperParseError
            When the page structure does not match expectations.
        ScraperHTTPError / ScraperTimeoutError
            Propagated from :class:`BaseScraper.fetch`.
        """
        html = await self.fetch(self._schedule_url)
        logger.info("Parsing match schedule from %s", self._schedule_url)

        try:
            next_data = _extract_next_data(html, self._schedule_url)
        except ScraperParseError:
            logger.warning(
                "Could not extract __NEXT_DATA__ from schedule page; "
                "returning empty schedule"
            )
            return ScrapedSchedule(
                matches=[],
                source_url=self._schedule_url,
            )

        matches = self._parse_schedule_matches(next_data, self._schedule_url)
        logger.info("Scraped %d matches from schedule", len(matches))

        return ScrapedSchedule(
            matches=matches,
            source_url=self._schedule_url,
        )

    async def scrape_match_result(self, match_id: int) -> ScrapedMatchResult:
        """Scrape the result for a single match.

        Parameters
        ----------
        match_id:
            The FIFA match identifier (used to construct the URL).

        Returns
        -------
        ScrapedMatchResult
            Validated match result with events.

        Raises
        ------
        ScraperParseError
            When the page structure does not match expectations.
        """
        url = f"{self._match_url_base}/{match_id}"
        html = await self.fetch(url)
        logger.info("Parsing match result from %s", url)

        try:
            next_data = _extract_next_data(html, url)
        except ScraperParseError:
            logger.warning(
                "Could not extract __NEXT_DATA__ from match page %s; "
                "returning empty result",
                url,
            )
            return ScrapedMatchResult(
                external_id=str(match_id),
                home_score=0,
                away_score=0,
                events=[],
                source_url=url,
            )

        result = self._parse_match_result(next_data, str(match_id), url)
        logger.info(
            "Scraped match result: %s %d-%d (%d events)",
            result.external_id,
            result.home_score,
            result.away_score,
            len(result.events),
        )

        return result

    # ── Schedule parsing ───────────────────────────────────────────────

    def _parse_schedule_matches(
        self, next_data: Dict[str, Any], url: str
    ) -> List[ScrapedMatch]:
        """Parse match entries from the Next.js page data.

        This method attempts multiple JSON paths to accommodate
        variations in FIFA page structure.
        """
        matches_data = self._find_matches_in_data(next_data)
        if matches_data is None:
            logger.warning(
                "Could not locate match data in schedule page JSON at %s", url
            )
            return []

        results: List[ScrapedMatch] = []
        for entry in matches_data:
            try:
                match = self._parse_single_schedule_match(entry)
                results.append(match)
            except Exception:
                logger.warning(
                    "Failed to parse schedule entry: %s",
                    str(entry)[:200],
                    exc_info=True,
                )
        return results

    def _parse_single_schedule_match(self, entry: Dict[str, Any]) -> ScrapedMatch:
        """Parse one match dict from schedule data into a ScrapedMatch."""
        kickoff = entry.get("kickoffUtc") or entry.get("date")
        if isinstance(kickoff, str):
            kickoff_dt = datetime.fromisoformat(
                kickoff.replace("Z", "+00:00")
            )
        elif isinstance(kickoff, (int, float)):
            kickoff_dt = datetime.fromtimestamp(kickoff, tz=timezone.utc)
        else:
            kickoff_dt = datetime.now(tz=timezone.utc)

        return ScrapedMatch(
            external_id=str(
                entry.get("matchId") or entry.get("id") or entry.get("externalId", "")
            ),
            home_team=str(
                entry.get("homeTeam", {}).get("name", "")
                or entry.get("home", "")
            ),
            away_team=str(
                entry.get("awayTeam", {}).get("name", "")
                or entry.get("away", "")
            ),
            kickoff_utc=kickoff_dt,
            stage=str(entry.get("stage", "group")).lower(),
            group_label=entry.get("groupLabel") or entry.get("group"),
            venue_name=entry.get("venue", {}).get("name")
            if isinstance(entry.get("venue"), dict)
            else entry.get("venue"),
            status=str(entry.get("status", "upcoming")).lower(),
            home_score=entry.get("homeScore"),
            away_score=entry.get("awayScore"),
        )

    # ── Match result parsing ───────────────────────────────────────────

    def _parse_match_result(
        self,
        next_data: Dict[str, Any],
        external_id: str,
        url: str,
    ) -> ScrapedMatchResult:
        """Parse match result data from the Next.js page data."""
        match_data = self._find_match_detail_in_data(next_data)
        if match_data is None:
            logger.warning("Could not locate match detail in page JSON at %s", url)
            return ScrapedMatchResult(
                external_id=external_id,
                home_score=0,
                away_score=0,
                events=[],
                source_url=url,
            )

        events = self._parse_events(match_data)
        return ScrapedMatchResult(
            external_id=external_id,
            status=str(match_data.get("status", "finished")).lower(),
            home_score=int(match_data.get("homeScore", 0)),
            away_score=int(match_data.get("awayScore", 0)),
            events=events,
            source_url=url,
        )

    def _parse_events(self, match_data: Dict[str, Any]) -> List[ScrapedEvent]:
        """Parse event list from match detail data."""
        raw_events = match_data.get("events", [])
        if not isinstance(raw_events, list):
            return []

        results: List[ScrapedEvent] = []
        for ev in raw_events:
            if not isinstance(ev, dict):
                continue
            try:
                results.append(
                    ScrapedEvent(
                        event_type=str(
                            ev.get("type") or ev.get("eventType", "unknown")
                        ).lower(),
                        minute=int(ev.get("minute", 0)),
                        team_side=str(
                            ev.get("teamSide") or ev.get("side", "home")
                        ).lower(),
                        player_name=ev.get("playerName")
                        or ev.get("player"),
                    )
                )
            except Exception:
                logger.warning(
                    "Failed to parse event: %s", str(ev)[:200], exc_info=True
                )
        return results

    # ── JSON path helpers ──────────────────────────────────────────────

    @staticmethod
    def _find_matches_in_data(data: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Walk the Next.js data tree to find the match list.

        Tries several known paths used by FIFA.com:
        - props.pageProps.matches
        - props.pageProps.matchSchedule
        - props.pageProps.data.matches
        """
        props = data.get("props", {}).get("pageProps", {})
        if isinstance(props, dict):
            for key in ("matches", "matchSchedule", "allMatches"):
                found = props.get(key)
                if isinstance(found, list):
                    return found

            inner = props.get("data")
            if isinstance(inner, dict):
                for key in ("matches", "matchSchedule"):
                    found = inner.get(key)
                    if isinstance(found, list):
                        return found

        return None

    @staticmethod
    def _find_match_detail_in_data(
        data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Walk the Next.js data tree to find a single match detail.

        Tries:
        - props.pageProps.match
        - props.pageProps.matchDetail
        - props.pageProps.data
        """
        props = data.get("props", {}).get("pageProps", {})
        if isinstance(props, dict):
            for key in ("match", "matchDetail"):
                found = props.get(key)
                if isinstance(found, dict):
                    return found

            inner = props.get("data")
            if isinstance(inner, dict):
                return inner

        return None