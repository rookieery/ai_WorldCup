"""Match business logic — bridges controllers and MatchRepository / MatchEventRepository."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, Dict, Optional, Sequence

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.redis.keys import RedisKeys
from app.repositories.match_event_repo import MatchEventRepository
from app.repositories.match_repo import MatchRepository
from app.schemas.match_schema import (
    MatchDetailResponse,
    MatchEventResponse,
    MatchQueryParams,
    MatchResponse,
)
from app.utils.timezone import utc_to_local as _utc_to_local

logger = logging.getLogger(__name__)


class MatchService:
    """Orchestrates match-related business operations.

    Parameters
    ----------
    session:
        An ``AsyncSession`` managed by the caller (dependency injection).
    redis:
        An optional ``redis.asyncio.Redis`` instance.  When provided and
        available, live data from Redis overrides DB values for score,
        status, and activity_level.
    """

    def __init__(
        self,
        session: AsyncSession,
        redis: Optional[Redis] = None,
    ) -> None:
        self._match_repo = MatchRepository(session)
        self._event_repo = MatchEventRepository(session)
        self._redis = redis

    # ── public methods ─────────────────────────────────────────────────────

    async def get_match_dates(self) -> list[dict]:
        """Return all distinct match dates with their primary stage label.

        Each item contains ``date`` (ISO-8601) and ``stage``.
        """
        rows = await self._match_repo.get_match_dates()
        return [{"date": str(d), "stage": s} for d, s in rows]

    async def get_matches(
        self,
        *,
        params: MatchQueryParams,
        timezone_name: Optional[str] = None,
        lang: str = "en",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        """Return a filtered, paginated list of matches.

        Filter priority when multiple params are provided:
        date > team > group > stage > status.

        Returns
        -------
        (items_vo, total)
            A list of match value-object dicts and the total count.
        """
        matches: Sequence
        total: int

        if params.date:
            target_date = date.fromisoformat(params.date)
            matches, total = await self._match_repo.get_by_date(
                target_date, page=page, page_size=page_size
            )
            matches, total = self._apply_secondary_filters(
                matches, total, params, primary="date"
            )
        elif params.team:
            matches, total = await self._match_repo.get_by_team_code(
                params.team.upper(), page=page, page_size=page_size
            )
            matches, total = self._apply_secondary_filters(
                matches, total, params, primary="team"
            )
        elif params.group:
            matches, total = await self._match_repo.get_by_group_label(
                params.group.upper(), page=page, page_size=page_size
            )
            matches, total = self._apply_secondary_filters(
                matches, total, params, primary="group"
            )
        elif params.stage:
            matches, total = await self._match_repo.get_by_stage(
                params.stage, page=page, page_size=page_size
            )
            matches, total = self._apply_secondary_filters(
                matches, total, params, primary="stage"
            )
        elif params.status:
            matches, total = await self._match_repo.get_by_status(
                params.status, page=page, page_size=page_size
            )
        else:
            matches, total = await self._match_repo.get_all(
                page=page, page_size=page_size, order_by="kickoff_utc"
            )

        items_vo = [
            _match_to_vo(m, lang=lang, timezone_name=timezone_name)
            for m in matches
        ]

        # Merge Redis live data when available
        if self._redis is not None and items_vo:
            await self._merge_live_data_batch(items_vo)

        return items_vo, total

    async def get_match_by_id(
        self,
        match_id: int,
        *,
        timezone_name: Optional[str] = None,
        lang: str = "en",
    ) -> dict:
        """Return a single match with its events.

        Raises ``NotFoundError`` when the match does not exist.
        """
        match = await self._match_repo.get_by_id(match_id)
        events = await self._event_repo.get_by_match(match_id)
        result = _match_detail_to_vo(match, events, lang=lang, timezone_name=timezone_name)

        # Merge Redis live data when available
        if self._redis is not None:
            live_data = await self._get_live_data_from_redis(match_id)
            if live_data is not None:
                _apply_live_override(result, live_data)

        return result

    async def get_live_matches(
        self,
        *,
        timezone_name: Optional[str] = None,
        lang: str = "en",
    ) -> list[dict]:
        """Return all currently live matches.

        When Redis is available, live data from Redis overrides the DB
        values for score, status, and activity_level.  The base match
        list still comes from the database.
        """
        matches = await self._match_repo.get_live_matches()
        items_vo = [
            _match_to_vo(m, lang=lang, timezone_name=timezone_name)
            for m in matches
        ]

        # Merge Redis live data when available
        if self._redis is not None and items_vo:
            await self._merge_live_data_batch(items_vo)

        return items_vo

    # ── private helpers ────────────────────────────────────────────────────

    async def _merge_live_data_batch(
        self, items_vo: list[dict]
    ) -> None:
        """Fetch live data for multiple matches from Redis and merge into VOs."""
        try:
            pipe = self._redis.pipeline(transaction=False)
            for item in items_vo:
                key = RedisKeys.LIVE_MATCH.format(match_id=item["id"])
                pipe.hgetall(key)
            results = await pipe.execute()

            for item, data in zip(items_vo, results):
                if data:
                    _apply_live_override(item, data)
        except Exception:
            logger.warning(
                "Failed to merge live data from Redis", exc_info=True
            )

    async def _get_live_data_from_redis(
        self, match_id: int
    ) -> Optional[Dict[str, Any]]:
        """Fetch live data for a single match from Redis."""
        try:
            key = RedisKeys.LIVE_MATCH.format(match_id=match_id)
            data = await self._redis.hgetall(key)
            return data if data else None
        except Exception:
            logger.warning(
                "Failed to fetch live data for match %d from Redis",
                match_id,
                exc_info=True,
            )
            return None

    @staticmethod
    def _apply_secondary_filters(
        matches: Sequence,
        total: int,
        params: MatchQueryParams,
        primary: str,
    ) -> tuple[list, int]:
        """Apply remaining filters in-memory after the primary repo query."""
        result = list(matches)

        if primary != "date" and params.date:
            target = date.fromisoformat(params.date)
            result = [m for m in result if m.kickoff_utc.date() == target]

        if primary != "team" and params.team:
            code = params.team.upper()
            result = [
                m
                for m in result
                if m.home_team.code == code or m.away_team.code == code
            ]

        if primary != "group" and params.group:
            gl = params.group.upper()
            result = [m for m in result if m.group_label == gl]

        if primary != "stage" and params.stage:
            result = [m for m in result if m.stage == params.stage]

        if primary != "status" and params.status:
            result = [m for m in result if m.status == params.status]

        return result, len(result)


# ── module-level helpers ──────────────────────────────────────────────────


def _match_to_vo(
    match: object,
    *,
    lang: str = "en",
    timezone_name: Optional[str] = None,
) -> dict:
    """Convert a Match ORM object into a MatchResponse dict."""
    data = MatchResponse.model_validate(match).model_dump()

    _apply_team_lang(data, "home_team", lang)
    _apply_team_lang(data, "away_team", lang)
    _apply_venue_lang(data, lang)

    if timezone_name:
        try:
            data["local_time"] = _utc_to_local(match.kickoff_utc, timezone_name)
        except Exception:
            data["local_time"] = None

    if match.venue and match.venue.timezone:
        try:
            data["host_time"] = _utc_to_local(
                match.kickoff_utc, match.venue.timezone
            )
        except Exception:
            data["host_time"] = None

    return data


def _match_detail_to_vo(
    match: object,
    events: Sequence,
    *,
    lang: str = "en",
    timezone_name: Optional[str] = None,
) -> dict:
    """Convert a Match ORM object + events into a MatchDetailResponse dict."""
    data = MatchDetailResponse.model_validate(match).model_dump()

    _apply_team_lang(data, "home_team", lang)
    _apply_team_lang(data, "away_team", lang)
    _apply_venue_lang(data, lang)

    event_vos = [MatchEventResponse.model_validate(e).model_dump() for e in events]
    data["events"] = event_vos

    if timezone_name:
        try:
            data["local_time"] = _utc_to_local(match.kickoff_utc, timezone_name)
        except Exception:
            data["local_time"] = None

    if match.venue and match.venue.timezone:
        try:
            data["host_time"] = _utc_to_local(
                match.kickoff_utc, match.venue.timezone
            )
        except Exception:
            data["host_time"] = None

    return data


def _apply_team_lang(data: dict, team_key: str, lang: str) -> None:
    """Promote ``name_zh`` to ``name`` when language is Chinese."""
    if lang == "zh" and team_key in data and data[team_key]:
        team_data = data[team_key]
        team_data["name"] = team_data.get("name_zh", team_data["name"])


def _apply_venue_lang(data: dict, lang: str) -> None:
    """Promote ``name_zh``, ``city_zh``, ``country_zh`` when language is Chinese."""
    if lang == "zh" and "venue" in data and data["venue"]:
        venue = data["venue"]
        venue["name"] = venue.get("name_zh") or venue["name"]
        venue["city"] = venue.get("city_zh") or venue["city"]
        venue["country"] = venue.get("country_zh") or venue["country"]


def _apply_live_override(
    vo: dict, live_data: Dict[str, Any]
) -> None:
    """Overlay Redis live data onto a match value-object dict in-place.

    Only overrides fields that exist in the live data hash:
    ``status``, ``home_score``, ``away_score``, ``activity_level`` (mapped
    from the Redis ``activity`` field).

    Redis HASH values are always strings, so they are coerced to the
    expected types.
    """
    if "status" in live_data:
        vo["status"] = live_data["status"]

    if "home_score" in live_data:
        vo["home_score"] = int(live_data["home_score"])

    if "away_score" in live_data:
        vo["away_score"] = int(live_data["away_score"])

    if "activity" in live_data:
        vo["activity_level"] = int(live_data["activity"])
