"""Team business logic — bridges controllers and TeamRepository."""

from __future__ import annotations

from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.team_repo import TeamRepository
from app.schemas.team_schema import TeamListResponse, TeamResponse


class TeamService:
    """Orchestrates team-related business operations.

    Parameters
    ----------
    session:
        An ``AsyncSession`` managed by the caller (dependency injection).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._repo = TeamRepository(session)

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
