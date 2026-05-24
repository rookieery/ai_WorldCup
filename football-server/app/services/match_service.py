"""Match business logic — bridges controllers and MatchRepository / MatchEventRepository."""

from __future__ import annotations

from datetime import date
from typing import Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.match_event_repo import MatchEventRepository
from app.repositories.match_repo import MatchRepository
from app.schemas.match_schema import (
    MatchDetailResponse,
    MatchEventResponse,
    MatchQueryParams,
    MatchResponse,
)
from app.utils.timezone import utc_to_local as _utc_to_local


class MatchService:
    """Orchestrates match-related business operations.

    Parameters
    ----------
    session:
        An ``AsyncSession`` managed by the caller (dependency injection).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._match_repo = MatchRepository(session)
        self._event_repo = MatchEventRepository(session)

    # ── public methods ─────────────────────────────────────────────────────

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
        return _match_detail_to_vo(match, events, lang=lang, timezone_name=timezone_name)

    async def get_live_matches(
        self,
        *,
        timezone_name: Optional[str] = None,
        lang: str = "en",
    ) -> list[dict]:
        """Return all currently live matches."""
        matches = await self._match_repo.get_live_matches()
        return [
            _match_to_vo(m, lang=lang, timezone_name=timezone_name)
            for m in matches
        ]

    # ── private helpers ────────────────────────────────────────────────────

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
