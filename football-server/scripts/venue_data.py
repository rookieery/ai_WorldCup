"""Venue data for the 2026 FIFA World Cup seed script.

Contains the complete 16-stadium roster with city, country, IANA timezone,
standard UTC offset, and seating capacity.

All 16 venues are spread across three host nations:
- United States (11 stadiums)
- Canada (2 stadiums)
- Mexico (3 stadiums)
"""

from __future__ import annotations

from typing import Any

VENUES: list[dict[str, Any]] = [
    # ── United States (11 venues) ────────────────────────────────────────
    {
        "name": "MetLife Stadium",
        "city": "East Rutherford",
        "country": "United States",
        "timezone": "America/New_York",
        "utc_offset": "-05:00",
        "capacity": 87000,
    },
    {
        "name": "AT&T Stadium",
        "city": "Arlington",
        "country": "United States",
        "timezone": "America/Chicago",
        "utc_offset": "-06:00",
        "capacity": 80000,
    },
    {
        "name": "SoFi Stadium",
        "city": "Inglewood",
        "country": "United States",
        "timezone": "America/Los_Angeles",
        "utc_offset": "-08:00",
        "capacity": 70000,
    },
    {
        "name": "Hard Rock Stadium",
        "city": "Miami Gardens",
        "country": "United States",
        "timezone": "America/New_York",
        "utc_offset": "-05:00",
        "capacity": 65000,
    },
    {
        "name": "Mercedes-Benz Stadium",
        "city": "Atlanta",
        "country": "United States",
        "timezone": "America/New_York",
        "utc_offset": "-05:00",
        "capacity": 71000,
    },
    {
        "name": "Lincoln Financial Field",
        "city": "Philadelphia",
        "country": "United States",
        "timezone": "America/New_York",
        "utc_offset": "-05:00",
        "capacity": 69000,
    },
    {
        "name": "Lumen Field",
        "city": "Seattle",
        "country": "United States",
        "timezone": "America/Los_Angeles",
        "utc_offset": "-08:00",
        "capacity": 69000,
    },
    {
        "name": "Gillette Stadium",
        "city": "Foxborough",
        "country": "United States",
        "timezone": "America/New_York",
        "utc_offset": "-05:00",
        "capacity": 65000,
    },
    {
        "name": "NRG Stadium",
        "city": "Houston",
        "country": "United States",
        "timezone": "America/Chicago",
        "utc_offset": "-06:00",
        "capacity": 72000,
    },
    {
        "name": "Arrowhead Stadium",
        "city": "Kansas City",
        "country": "United States",
        "timezone": "America/Chicago",
        "utc_offset": "-06:00",
        "capacity": 76000,
    },
    {
        "name": "Levi's Stadium",
        "city": "Santa Clara",
        "country": "United States",
        "timezone": "America/Los_Angeles",
        "utc_offset": "-08:00",
        "capacity": 68000,
    },
    # ── Canada (2 venues) ────────────────────────────────────────────────
    {
        "name": "BMO Field",
        "city": "Toronto",
        "country": "Canada",
        "timezone": "America/Toronto",
        "utc_offset": "-05:00",
        "capacity": 45000,
    },
    {
        "name": "BC Place",
        "city": "Vancouver",
        "country": "Canada",
        "timezone": "America/Vancouver",
        "utc_offset": "-08:00",
        "capacity": 54000,
    },
    # ── Mexico (3 venues) ────────────────────────────────────────────────
    {
        "name": "Estadio Azteca",
        "city": "Mexico City",
        "country": "Mexico",
        "timezone": "America/Mexico_City",
        "utc_offset": "-06:00",
        "capacity": 87000,
    },
    {
        "name": "Estadio BBVA",
        "city": "Monterrey",
        "country": "Mexico",
        "timezone": "America/Monterrey",
        "utc_offset": "-06:00",
        "capacity": 53000,
    },
    {
        "name": "Estadio Akron",
        "city": "Guadalajara",
        "country": "Mexico",
        "timezone": "America/Mexico_City",
        "utc_offset": "-06:00",
        "capacity": 49000,
    },
]