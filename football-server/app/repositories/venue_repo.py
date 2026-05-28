"""Venue-specific repository — simple CRUD, no custom queries needed."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.venue import Venue
from app.repositories.base import BaseRepository


class VenueRepository(BaseRepository[Venue]):
    """Data access for ``venues`` table."""

    model = Venue

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)
