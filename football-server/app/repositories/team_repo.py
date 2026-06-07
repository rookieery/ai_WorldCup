"""Team-specific repository — adds lookups by code, name, and group."""

from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team import Team
from app.repositories.base import BaseRepository


class TeamRepository(BaseRepository[Team]):
    """Data access for ``teams`` table."""

    model = Team

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_code(self, code: str) -> Team:
        """Return a team by its unique 3-letter code.

        Raises ``NotFoundError`` when the code does not exist.
        """
        stmt = select(self.model).where(self.model.code == code)
        result = await self.session.execute(stmt)
        team = result.unique().scalar_one_or_none()
        if team is None:
            from app.exceptions.exceptions import NotFoundError

            raise NotFoundError(f"Team with code={code!r} not found")
        return team

    async def search_by_name(self, name_query: str) -> Optional[Team]:
        """Return a team matching *name_query* against code, name, or name_zh.

        Performs case-insensitive matching on ``code`` and ``name``, and
        exact matching on ``name_zh`` (Chinese team names are short and
        unambiguous).
        """
        stmt = select(self.model).where(
            or_(
                self.model.code == name_query.upper(),
                self.model.name.ilike(f"%{name_query}%"),
                self.model.name_zh == name_query,
            )
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_by_group(self, group_label: str) -> Sequence[Team]:
        """Return all teams belonging to a group letter (e.g. ``"A"``)."""
        stmt = (
            select(self.model)
            .where(self.model.group_label == group_label)
            .order_by(self.model.fifa_ranking.asc())
        )
        result = await self.session.execute(stmt)
        return result.unique().scalars().all()
