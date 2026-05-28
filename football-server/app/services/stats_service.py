"""Stats business logic — scorer leaderboard, match statistics."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.match_event_repo import MatchEventRepository

logger = logging.getLogger(__name__)


class StatsService:
    """Orchestrates statistics-related business operations.

    Parameters
    ----------
    session:
        An ``AsyncSession`` managed by the caller (dependency injection).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._event_repo = MatchEventRepository(session)

    async def get_scorers(
        self,
        *,
        lang: str = "en",
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Return the scorer leaderboard.

        Aggregates goal events per player and enriches with team info.

        Returns
        -------
        list[dict]
            A list of scorer dicts ready for the response VO.
        """
        rows = await self._event_repo.get_scorers_leaderboard(limit=limit)

        scorers: list[dict[str, Any]] = []
        for idx, row in enumerate(rows, start=1):
            scorers.append({
                "rank": idx,
                "player_name": row.player_name,
                "team_code": row.team_code,
                "team_name": row.team_name if lang == "en" else row.team_name_zh,
                "team_name_zh": row.team_name_zh,
                "team_flag": row.team_flag,
                "goals": row.goals,
                "assists": 0,
            })

        return scorers
