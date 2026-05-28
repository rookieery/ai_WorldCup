"""Common generic response schemas used across all API endpoints."""

from __future__ import annotations

from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Unified JSON envelope for every API response.

    Shape: ``{ "code": int, "data": T | null, "message": str }``
    """

    code: int = Field(default=200, description="HTTP-equivalent status code")
    data: Optional[T] = Field(default=None, description="Response payload")
    message: str = Field(default="success", description="Human-readable status message")

    model_config = {"from_attributes": True}


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list payload returned inside ``ApiResponse.data``.

    Provides metadata (total, page, page_size) alongside the slice of items.
    """

    items: List[T] = Field(default_factory=list, description="Current page of results")
    total: int = Field(default=0, description="Total number of records")
    page: int = Field(default=1, ge=1, description="Current page number (1-based)")
    page_size: int = Field(
        default=20, ge=1, le=100, description="Number of items per page"
    )

    model_config = {"from_attributes": True}
