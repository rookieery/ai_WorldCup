"""Group business logic — bridges controllers and GroupRepository / MatchRepository."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from zoneinfo import ZoneInfo

from app.exceptions.exceptions import NotFoundError
from app.repositories.group_repo import GroupRepository
from app.repositories.match_repo import MatchRepository
from app.schemas.group_schema import GroupStandingResponse


class GroupService:
    """Orchestrates group-related business operations.

    Parameters
    ----------
    session:
        An ``AsyncSession`` managed by the caller (dependency injection).
    """

    _VALID_GROUPS = tuple("ABCDEFGHIJKL")

    def __init__(self, session: AsyncSession) -> None:
        self._group_repo = GroupRepository(session)
        self._match_repo = MatchRepository(session)

    # ── public methods ─────────────────────────────────────────────────────

    async def get_all_groups(
        self,
        *,
        lang: str = "en",
    ) -> list[dict]:
        """Return an overview list for all 12 groups (A-L).

        Each entry contains ``group_label`` and ``standings`` sorted by
        points desc → goal_difference desc → goals_for desc.
        """
        result: list[dict] = []
        for label in self._VALID_GROUPS:
            standings = await self._group_repo.get_by_group_label(label)
            standings_vo = [_standing_to_vo(s, lang) for s in standings]
            result.append({
                "group_label": label,
                "standings": standings_vo,
            })
        return result

    async def get_group_detail(
        self,
        group_label: str,
        *,
        timezone_name: Optional[str] = None,
        lang: str = "en",
    ) -> dict:
        """Return standings + matches for a single group.

        Raises ``NotFoundError`` when the group label is not A-L.
        """
        label = group_label.upper()
        if label not in self._VALID_GROUPS:
            raise NotFoundError(f"Group '{group_label}' is not a valid group (A-L)")

        standings = await self._group_repo.get_by_group_label(label)
        matches = await self._group_repo.get_group_matches(label)

        standings_vo = [_standing_to_vo(s, lang) for s in standings]
        matches_vo = [_match_to_vo(m, lang=lang, timezone_name=timezone_name) for m in matches]

        return {
            "group_label": label,
            "standings": standings_vo,
            "matches": matches_vo,
        }


# ── module-level helpers ──────────────────────────────────────────────────


def _standing_to_vo(standing: object, lang: str) -> dict:
    """Convert a GroupStanding ORM object into a response dict."""
    data = GroupStandingResponse.model_validate(standing).model_dump()
    _apply_team_lang(data, "team", lang)
    return data


def _match_to_vo(
    match: object,
    *,
    lang: str = "en",
    timezone_name: Optional[str] = None,
) -> dict:
    """Convert a Match ORM object into a simplified dict for group detail."""
    from app.schemas.match_schema import MatchResponse

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
            data["host_time"] = _utc_to_local(match.kickoff_utc, match.venue.timezone)
        except Exception:
            data["host_time"] = None

    return data


def _utc_to_local(utc_dt: datetime, target_tz: str) -> str:
    """Convert a UTC datetime to a time string in the target timezone."""
    aware_utc = utc_dt.replace(tzinfo=ZoneInfo("UTC"))
    local_dt = aware_utc.astimezone(ZoneInfo(target_tz))
    return local_dt.strftime("%H:%M")


def _apply_team_lang(data: dict, team_key: str, lang: str) -> None:
    """Promote ``name_zh`` to ``name`` when language is Chinese."""
    if lang == "zh" and team_key in data and data[team_key]:
        team_data = data[team_key]
        team_data["name"] = team_data.get("name_zh", team_data["name"])
