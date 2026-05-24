"""GroupStanding-specific repository — group label lookups and match queries."""

from __future__ import annotations

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group_standing import GroupStanding
from app.models.match import Match
from app.repositories.base import BaseRepository


class GroupRepository(BaseRepository[GroupStanding]):
    """Data access for ``group_standings`` table."""

    model = GroupStanding

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_group_label(self, group_label: str) -> Sequence[GroupStanding]:
        """Return all standings rows for a group, ordered by position."""
        stmt = (
            select(self.model)
            .where(self.model.group_label == group_label)
            .order_by(
                self.model.points.desc(),
                self.model.goal_difference.desc(),
                self.model.goals_for.desc(),
            )
        )
        result = await self.session.execute(stmt)
        return result.unique().scalars().all()

    async def get_group_matches(self, group_label: str) -> Sequence[Match]:
        """Return all group-stage matches for a specific group letter."""
        stmt = (
            select(Match)
            .where(
                Match.group_label == group_label,
                Match.stage == "group",
            )
            .order_by(Match.kickoff_utc.asc())
        )
        result = await self.session.execute(stmt)
        return result.unique().scalars().all()
