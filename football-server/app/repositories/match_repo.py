"""Match-specific repository — adds date / stage / status / bracket queries."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, Optional, Sequence

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.match import Match
from app.repositories.base import BaseRepository


class MatchRepository(BaseRepository[Match]):
    """Data access for ``matches`` table."""

    model = Match

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    # ── base query with eager loads ──────────────────────────────────────

    def _base_query(self) -> Select:
        return (
            select(self.model)
        )

    # ── custom lookups ───────────────────────────────────────────────────

    async def get_by_date(
        self,
        target_date: date,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[Match], int]:
        """Return matches whose ``kickoff_utc`` falls on *target_date* (UTC)."""
        start = datetime(target_date.year, target_date.month, target_date.day)
        end = datetime(
            target_date.year, target_date.month, target_date.day, 23, 59, 59
        )
        stmt = self._base_query().where(
            and_(
                self.model.kickoff_utc >= start,
                self.model.kickoff_utc <= end,
            )
        )
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar_one()

        offset = (page - 1) * page_size
        result = await self.session.execute(
            stmt.order_by(self.model.kickoff_utc.asc()).offset(offset).limit(page_size)
        )
        return result.unique().scalars().all(), total

    async def get_by_stage(
        self,
        stage: str,
        *,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[Sequence[Match], int]:
        """Return all matches for a given stage (group / R32 / R16 / …)."""
        stmt = self._base_query().where(self.model.stage == stage)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar_one()

        offset = (page - 1) * page_size
        result = await self.session.execute(
            stmt.order_by(self.model.kickoff_utc.asc()).offset(offset).limit(page_size)
        )
        return result.unique().scalars().all(), total

    async def get_by_status(
        self,
        status: str,
        *,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[Sequence[Match], int]:
        """Return matches filtered by status (upcoming / live / finished / postponed)."""
        stmt = self._base_query().where(self.model.status == status)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar_one()

        offset = (page - 1) * page_size
        result = await self.session.execute(
            stmt.order_by(self.model.kickoff_utc.asc()).offset(offset).limit(page_size)
        )
        return result.unique().scalars().all(), total

    async def get_live_matches(self) -> Sequence[Match]:
        """Return all currently live matches."""
        stmt = (
            self._base_query()
            .where(self.model.status == "live")
            .order_by(self.model.kickoff_utc.asc())
        )
        result = await self.session.execute(stmt)
        return result.unique().scalars().all()

    async def get_bracket_matches(self) -> Sequence[Match]:
        """Return all knockout-stage matches ordered for bracket rendering.

        Results are ordered by stage precedence then kickoff_utc.
        """
        knockout_stages = ["R32", "R16", "QF", "SF", "3rd", "F"]
        stmt = (
            self._base_query()
            .where(self.model.stage.in_(knockout_stages))
            .order_by(
                self.model.stage.asc(),
                self.model.kickoff_utc.asc(),
            )
        )
        result = await self.session.execute(stmt)
        return result.unique().scalars().all()

    async def get_by_group_label(
        self,
        group_label: str,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[Match], int]:
        """Return all group-stage matches for a specific group letter."""
        stmt = self._base_query().where(
            and_(
                self.model.group_label == group_label,
                self.model.stage == "group",
            )
        )
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar_one()

        offset = (page - 1) * page_size
        result = await self.session.execute(
            stmt.order_by(self.model.kickoff_utc.asc()).offset(offset).limit(page_size)
        )
        return result.unique().scalars().all(), total

    async def get_by_team_code(
        self,
        team_code: str,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[Match], int]:
        """Return all matches featuring a team identified by code."""
        from app.models.team import Team

        stmt = (
            self._base_query()
            .join(Team, or_(
                self.model.home_team_id == Team.id,
                self.model.away_team_id == Team.id,
            ))
            .where(Team.code == team_code)
        )
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar_one()

        offset = (page - 1) * page_size
        result = await self.session.execute(
            stmt.order_by(self.model.kickoff_utc.asc()).offset(offset).limit(page_size)
        )
        return result.unique().scalars().all(), total
