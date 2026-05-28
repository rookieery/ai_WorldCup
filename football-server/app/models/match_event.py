"""MatchEvent ORM model – a discrete event during a match (goal, card, etc.)."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class MatchEvent(TimestampMixin, Base):
    """A discrete event recorded during a match (goal, card, substitution …)."""

    __tablename__ = "match_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("matches.id"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # goal / own_goal / penalty / yellow_card / red_card / substitution / var
    minute: Mapped[int] = mapped_column(Integer, nullable=False)
    team_side: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # home / away
    player_name: Mapped[Optional[str]] = mapped_column(
        String(150), nullable=True, default=None
    )

    # ── relationships ─────────────────────────────────────────────────
    match: Mapped["Match"] = relationship(  # noqa: F821
        "Match",
        back_populates="events",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<MatchEvent id={self.id} match_id={self.match_id} "
            f"type={self.event_type!r} min={self.minute}>"
        )
