"""MatchEvent-specific repository — lookup by match, scorer aggregation."""

from __future__ import annotations

from typing import Sequence

from sqlalchemy import select, func, case, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.match_event import MatchEvent
from app.models.match import Match
from app.models.team import Team
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

    async def get_scorers_leaderboard(
        self,
        *,
        limit: int = 50,
    ) -> Sequence:
        """Return aggregated scorer stats: goals + assists per player.

        Goals are events with type ``goal``, ``penalty``, or ``own_goal``.
        Assists are proxied from ``player_name`` on ``substitution`` events
        when the actual assist data is unavailable (fallback: 0).

        Returns rows with:
            player_name, team_code, team_name, team_name_zh, team_flag,
            goals, assists
        """
        goal_types = ["goal", "penalty"]

        # ── Goals aggregation ─────────────────────────────────────────────
        goals_stmt = (
            select(
                MatchEvent.player_name,
                MatchEvent.team_side,
                MatchEvent.match_id,
            )
            .where(
                and_(
                    MatchEvent.event_type.in_(goal_types),
                    MatchEvent.player_name.isnot(None),
                )
            )
        )

        # We need team info — join through Match -> Team
        goals_with_team = (
            select(
                MatchEvent.player_name.label("player_name"),
                func.count().label("goals"),
                case(
                    (MatchEvent.team_side == "home", Match.home_team_id),
                    else_=Match.away_team_id,
                ).label("team_id"),
            )
            .select_from(
                MatchEvent.__table__.join(
                    Match.__table__,
                    MatchEvent.match_id == Match.id,
                )
            )
            .where(
                and_(
                    MatchEvent.event_type.in_(goal_types),
                    MatchEvent.player_name.isnot(None),
                    MatchEvent.player_name != "",
                )
            )
            .group_by(
                MatchEvent.player_name,
                case(
                    (MatchEvent.team_side == "home", Match.home_team_id),
                    else_=Match.away_team_id,
                ),
            )
            .order_by(func.count().desc())
            .limit(limit)
        )

        # Join with Team to get team info
        final_stmt = (
            select(
                goals_with_team.c.player_name,
                goals_with_team.c.goals,
                Team.code.label("team_code"),
                Team.name.label("team_name"),
                Team.name_zh.label("team_name_zh"),
                Team.flag.label("team_flag"),
            )
            .select_from(
                goals_with_team.join(
                    Team.__table__,
                    goals_with_team.c.team_id == Team.id,
                )
            )
            .order_by(goals_with_team.c.goals.desc())
        )

        result = await self.session.execute(final_stmt)
        return result.all()
