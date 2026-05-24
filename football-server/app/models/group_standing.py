"""GroupStanding ORM model – cumulative group-stage standings for a team."""

from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class GroupStanding(TimestampMixin, Base):
    """One row in a group-stage standings table (one team per row)."""

    __tablename__ = "group_standings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("teams.id"), unique=True, nullable=False
    )
    group_label: Mapped[str] = mapped_column(String(1), nullable=False)
    played: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    won: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    drawn: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lost: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    goals_for: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    goals_against: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    goal_difference: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # ── relationships ─────────────────────────────────────────────────
    team: Mapped["Team"] = relationship(  # noqa: F821
        "Team",
        back_populates="standing",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<GroupStanding team_id={self.team_id} group={self.group_label!r} "
            f"pts={self.points} pos={self.position}>"
        )
