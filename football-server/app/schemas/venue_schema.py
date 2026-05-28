"""Venue VO (response) schema."""

from __future__ import annotations

from pydantic import BaseModel, Field


class VenueResponse(BaseModel):
    """VO returned when reading venue information."""

    id: int
    name: str
    name_zh: str = ""
    city: str
    city_zh: str = ""
    country: str
    country_zh: str = ""
    timezone: str = Field(description="IANA timezone identifier (e.g. America/New_York)")
    utc_offset: str = Field(description="UTC offset string (e.g. -05:00)")
    capacity: int = Field(default=0, ge=0, description="Stadium seating capacity")

    model_config = {"from_attributes": True}
