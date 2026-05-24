"""Team ORM model – represents one of the 48 participating national teams."""

from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, relationship, mapped_column

from app.models.base import Base, TimestampMixin


class Team(TimestampMixin, Base):
    """National team participating in the 2026 FIFA World Cup."""

    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name_zh: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(3), unique=True, nullable=False)
    flag: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    fifa_ranking: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    group_label: Mapped[str] = mapped_column(String(1), nullable=False)
    confederation: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    world_cup_appearances: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # ── relationships ─────────────────────────────────────────────────
    home_matches: Mapped[list["Match"]] = relationship(  # noqa: F821
        "Match",
        foreign_keys="Match.home_team_id",
        back_populates="home_team",
        lazy="selectin",
    )
    away_matches: Mapped[list["Match"]] = relationship(  # noqa: F821
        "Match",
        foreign_keys="Match.away_team_id",
        back_populates="away_team",
        lazy="selectin",
    )
    standing: Mapped["GroupStanding | None"] = relationship(  # noqa: F821
        "GroupStanding",
        back_populates="team",
        uselist=False,
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Team id={self.id} code={self.code!r} name={self.name!r}>"
