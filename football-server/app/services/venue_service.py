"""Venue business logic — bridges controllers and VenueRepository."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.venue_repo import VenueRepository
from app.schemas.venue_schema import VenueResponse


class VenueService:
    """Orchestrates venue-related business operations.

    Parameters
    ----------
    session:
        An ``AsyncSession`` managed by the caller (dependency injection).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._repo = VenueRepository(session)

    async def get_all_venues(
        self,
        *,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[dict], int]:
        """Return a paginated list of venues with timezone information.

        Returns
        -------
        (items_vo, total)
            A list of venue value-object dicts and the total count.
        """
        venues, total = await self._repo.get_all(
            page=page,
            page_size=page_size,
            order_by="country",
        )
        items_vo = [VenueResponse.model_validate(v).model_dump() for v in venues]
        return items_vo, total
