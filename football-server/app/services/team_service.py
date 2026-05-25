"""Team business logic — bridges controllers and TeamRepository."""

from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.match import Match
from app.models.team import Team
from app.repositories.team_repo import TeamRepository
from app.schemas.team_schema import (
    TeamListResponse,
    TeamMatchVO,
    TeamResponse,
    TeamStandingVO,
    TeamStatsResponse,
)
from app.utils.timezone import utc_to_local as _utc_to_local


class TeamService:
    """Orchestrates team-related business operations.

    Parameters
    ----------
    session:
        An ``AsyncSession`` managed by the caller (dependency injection).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._repo = TeamRepository(session)
        self._session = session

    async def get_all_teams(
        self,
        *,
        page: int = 1,
        page_size: int = 100,
        group: str | None = None,
        lang: str = "en",
    ) -> tuple[list[dict], int]:
        """Return a paginated list of teams.

        If *group* is provided, only teams in that group are returned.

        Returns
        -------
        (items_vo, total)
            A list of team value-object dicts and the total count.
        """
        filters: dict = {}
        if group:
            filters["group_label"] = group.upper()

        teams, total = await self._repo.get_all(
            page=page,
            page_size=page_size,
            filters=filters or None,
            order_by="group_label",
        )
        items_vo = [_team_to_vo(t, lang) for t in teams]
        return items_vo, total

    async def get_team_by_code(
        self,
        code: str,
        *,
        lang: str = "en",
    ) -> dict:
        """Return a single team by its 3-letter code.

        Raises ``NotFoundError`` when the code does not exist.
        """
        team = await self._repo.get_by_code(code.upper())
        return _team_to_vo(team, lang, full=True)

    async def get_teams_by_group(
        self,
        group_label: str,
        *,
        lang: str = "en",
    ) -> list[dict]:
        """Return all teams in a given group, ordered by FIFA ranking."""
        teams: Sequence = await self._repo.get_by_group(group_label.upper())
        return [_team_to_vo(t, lang) for t in teams]

    async def get_team_stats(
        self,
        code: str,
        *,
        lang: str = "en",
        timezone_name: Optional[str] = None,
    ) -> dict:
        """Return comprehensive statistics for a team identified by code.

        Aggregates team info, group standing, finished matches, and upcoming
        matches into a single response.

        Raises ``NotFoundError`` when the code does not exist.
        """
        team = await self._repo.get_by_code(code.upper())
        team_data = TeamStatsResponse.model_validate(team).model_dump()

        if lang == "zh":
            team_data["name"] = team_data["name_zh"]

        # ── Group standing ──────────────────────────────────────────────
        standing = team.standing
        if standing is not None:
            team_data["standing"] = TeamStandingVO.model_validate(standing).model_dump()

        # ── Matches (home + away) ───────────────────────────────────────
        all_matches = list(team.home_matches) + list(team.away_matches)
        finished_matches: list[dict] = []
        upcoming_matches: list[dict] = []

        for m in all_matches:
            match_vo = _match_to_team_vo(m, team.code, lang=lang, timezone_name=timezone_name)
            if m.status == "finished":
                finished_matches.append(match_vo)
            elif m.status in ("upcoming", "postponed"):
                upcoming_matches.append(match_vo)

        # Sort: finished by kickoff desc, upcoming by kickoff asc
        finished_matches.sort(key=lambda x: x["kickoff_utc"], reverse=True)
        upcoming_matches.sort(key=lambda x: x["kickoff_utc"])

        team_data["finished_matches"] = finished_matches
        team_data["upcoming_matches"] = upcoming_matches

        return team_data


# ── helpers ──────────────────────────────────────────────────────────────


def _team_to_vo(team: object, lang: str, *, full: bool = False) -> dict:
    """Convert a Team ORM object into a response dict.

    When *lang* is ``"zh"`` the ``name_zh`` value is promoted to ``name``
    so that callers always see the display name in ``name``.
    """
    data = TeamResponse.model_validate(team).model_dump()

    if lang == "zh":
        data["name"] = data["name_zh"]

    if not full:
        # Strip less-used fields for list responses
        list_fields = TeamListResponse.model_validate(team).model_dump()
        if lang == "zh":
            list_fields["name"] = data["name_zh"]
        return list_fields

    return data


def _match_to_team_vo(
    match: Match,
    team_code: str,
    *,
    lang: str = "en",
    timezone_name: Optional[str] = None,
) -> dict:
    """Convert a Match ORM object into a TeamMatchVO dict from the team's perspective."""
    is_home = match.home_team.code == team_code
    opponent = match.away_team if is_home else match.home_team
    score_for = match.home_score if is_home else match.away_score
    score_against = match.away_score if is_home else match.home_score

    opponent_name = opponent.name
    if lang == "zh":
        opponent_name = opponent.name_zh

    host_time: str | None = None
    if match.venue and match.venue.timezone:
        try:
            host_time = _utc_to_local(match.kickoff_utc, match.venue.timezone)
        except Exception:
            host_time = None

    vo = TeamMatchVO(
        id=match.id,
        opponent=opponent_name,
        opponent_code=opponent.code,
        opponent_flag=opponent.flag,
        home_away="home" if is_home else "away",
        score_for=score_for,
        score_against=score_against,
        kickoff_utc=match.kickoff_utc.isoformat(),
        host_time=host_time,
        venue_name=match.venue.name if match.venue else "",
        venue_city=match.venue.city if match.venue else "",
        status=match.status,
        stage=match.stage,
        group_label=match.group_label,
    )

    return vo.model_dump()
