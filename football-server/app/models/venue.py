"""Venue ORM model – represents one of the 16 host-city stadiums."""

from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, relationship, mapped_column

from app.models.base import Base, TimestampMixin


class Venue(TimestampMixin, Base):
    """Stadium / venue hosting World Cup matches."""

    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    name_zh: Mapped[str] = mapped_column(String(150), nullable=False, default="")
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    city_zh: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    country_zh: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    timezone: Mapped[str] = mapped_column(String(50), nullable=False)
    utc_offset: Mapped[str] = mapped_column(String(10), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # ── relationships ─────────────────────────────────────────────────
    matches: Mapped[list["Match"]] = relationship(  # noqa: F821
        "Match",
        back_populates="venue",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Venue id={self.id} name={self.name!r} city={self.city!r}>"
