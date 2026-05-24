"""MatchEvent-specific repository — lookup by match."""

from __future__ import annotations

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.match_event import MatchEvent
from app.repositories.base import BaseRepository


class MatchEventRepository(BaseRepository[MatchEvent]):
    """Data access for ``match_events`` table."""

    model = MatchEvent

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_match(self, match_id: int) -> Sequence[MatchEvent]:
        """Return all events for a match, ordered by minute."""
        stmt = (
            select(self.model)
            .where(self.model.match_id == match_id)
            .order_by(self.model.minute.asc(), self.model.id.asc())
        )
        result = await self.session.execute(stmt)
        return result.unique().scalars().all()
