"""Match ORM model – represents a single fixture (group stage or knockout)."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Match(TimestampMixin, Base):
    """A World Cup fixture – group stage or knockout round."""

    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False
    )

    # ── foreign keys ──────────────────────────────────────────────────
    home_team_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("teams.id"), nullable=False
    )
    away_team_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("teams.id"), nullable=False
    )
    venue_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("venues.id"), nullable=False
    )

    # ── fixture metadata ──────────────────────────────────────────────
    stage: Mapped[str] = mapped_column(String(20), nullable=False)  # group / R32 / R16 / QF / SF / 3rd / F
    group_label: Mapped[Optional[str]] = mapped_column(
        String(1), nullable=True, default=None
    )
    round: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    match_day: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=None
    )
    kickoff_utc: Mapped[datetime] = mapped_column(
        DateTime, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="upcoming"
    )  # upcoming / live / finished / postponed

    # ── scores ────────────────────────────────────────────────────────
    home_score: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=None
    )
    away_score: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=None
    )

    # ── display / engagement ──────────────────────────────────────────
    is_big_match: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    activity_level: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    # ── bracket linkage ───────────────────────────────────────────────
    next_match_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("matches.id"), nullable=True, default=None
    )
    position: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=None
    )  # 1 = home slot, 2 = away slot in next_match

    # ── relationships ─────────────────────────────────────────────────
    home_team: Mapped["Team"] = relationship(  # noqa: F821
        "Team",
        foreign_keys=[home_team_id],
        back_populates="home_matches",
        lazy="selectin",
    )
    away_team: Mapped["Team"] = relationship(  # noqa: F821
        "Team",
        foreign_keys=[away_team_id],
        back_populates="away_matches",
        lazy="selectin",
    )
    venue: Mapped["Venue"] = relationship(  # noqa: F821
        "Venue",
        back_populates="matches",
        lazy="selectin",
    )
    next_match: Mapped[Optional["Match"]] = relationship(
        "Match",
        remote_side=[id],
        foreign_keys=[next_match_id],
        lazy="selectin",
    )
    events: Mapped[list["MatchEvent"]] = relationship(  # noqa: F821
        "MatchEvent",
        back_populates="match",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Match id={self.id} ext={self.external_id!r} "
            f"stage={self.stage!r} status={self.status!r}>"
        )
