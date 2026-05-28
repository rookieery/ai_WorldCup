"""Generic async CRUD repository base for SQLAlchemy models.

Every public method is async and accepts an ``AsyncSession`` at
construction time so callers (services / dependencies) control the
session lifecycle.
"""

from __future__ import annotations

from typing import Any, Dict, Generic, List, Optional, Sequence, Type, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.exceptions import NotFoundError, ValidationError

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Async CRUD base repository.

    Subclasses **must** set ``model`` to the concrete SQLAlchemy model class.
    """

    model: Type[T]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── helpers ──────────────────────────────────────────────────────────

    def _base_query(self) -> Select:
        """Return a base ``select()`` for the model. Override to add
        default eager-load options."""
        return select(self.model)

    # ── read ─────────────────────────────────────────────────────────────

    async def get_by_id(self, entity_id: int) -> T:
        """Fetch a single row by primary key or raise ``NotFoundError``."""
        stmt = self._base_query().where(self.model.id == entity_id)  # type: ignore[attr-defined]
        result = await self.session.execute(stmt)
        entity = result.unique().scalar_one_or_none()
        if entity is None:
            raise NotFoundError(
                f"{self.model.__name__} with id={entity_id} not found"
            )
        return entity

    async def get_by_id_optional(self, entity_id: int) -> Optional[T]:
        """Fetch a single row by primary key, returning ``None`` if absent."""
        stmt = self._base_query().where(self.model.id == entity_id)  # type: ignore[attr-defined]
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_all(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
    ) -> tuple[Sequence[T], int]:
        """Return a paginated slice and the total count.

        Parameters
        ----------
        page:
            1-based page number.
        page_size:
            Number of rows per page (1–100).
        filters:
            Optional ``{column: value}`` equality predicates.
        order_by:
            Column name to order by (prefix with ``-`` for descending).

        Returns
        -------
        (items, total)
            A tuple of the result slice and total matching rows.
        """
        stmt = self._base_query()

        # Apply equality filters
        if filters:
            for col_name, value in filters.items():
                if value is not None and hasattr(self.model, col_name):
                    stmt = stmt.where(getattr(self.model, col_name) == value)

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        # Ordering
        if order_by:
            desc = order_by.startswith("-")
            col_name = order_by.lstrip("-")
            if hasattr(self.model, col_name):
                col = getattr(self.model, col_name)
                stmt = stmt.order_by(col.desc() if desc else col.asc())

        # Pagination
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        result = await self.session.execute(stmt)
        items = result.unique().scalars().all()

        return items, total

    # ── create ───────────────────────────────────────────────────────────

    async def create(self, data: Dict[str, Any]) -> T:
        """Persist a new row. Raises ``ValidationError`` on integrity errors."""
        entity = self.model(**data)  # type: ignore[call-arg]
        self.session.add(entity)
        try:
            await self.session.flush()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ValidationError(
                f"Duplicate or invalid data for {self.model.__name__}: {exc}"
            ) from exc
        return entity

    # ── update ───────────────────────────────────────────────────────────

    async def update(self, entity_id: int, data: Dict[str, Any]) -> T:
        """Partially update an existing row. Raises ``NotFoundError`` if absent."""
        entity = await self.get_by_id(entity_id)
        for key, value in data.items():
            if value is not None and hasattr(entity, key):
                setattr(entity, key, value)
        await self.session.flush()
        return entity

    # ── delete ───────────────────────────────────────────────────────────

    async def delete(self, entity_id: int) -> None:
        """Delete a row by primary key. Raises ``NotFoundError`` if absent."""
        entity = await self.get_by_id(entity_id)
        await self.session.delete(entity)
        await self.session.flush()
