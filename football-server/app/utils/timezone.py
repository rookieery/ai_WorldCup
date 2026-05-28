"""Timezone conversion helpers using the standard-library ``zoneinfo`` module.

No third-party dependencies are required — ``zoneinfo`` ships with Python 3.9+.
On older CPython builds the ``tzdata`` package is used as a fallback data source.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from zoneinfo import ZoneInfo


def utc_to_local(utc_dt: datetime, target_tz: str) -> str:
    """Convert a UTC ``datetime`` to a time string in *target_tz*.

    Parameters
    ----------
    utc_dt:
        A ``datetime`` object interpreted as UTC.  If the object is
        timezone-naive it will be assumed to be UTC.
    target_tz:
        An IANA timezone name (e.g. ``"America/New_York"``).

    Returns
    -------
    str
        The local time formatted as ``HH:MM``.
    """
    aware_utc = utc_dt.replace(tzinfo=ZoneInfo("UTC"))
    local_dt = aware_utc.astimezone(ZoneInfo(target_tz))
    return local_dt.strftime("%H:%M")


def get_host_city_time(utc_dt: datetime, venue_timezone: str) -> str:
    """Return the venue's local kick-off time as ``HH:MM``.

    This is a convenience wrapper around :func:`utc_to_local` specialised for
    stadium / host-city use-cases.

    Parameters
    ----------
    utc_dt:
        Kick-off time in UTC (timezone-naive datetimes are treated as UTC).
    venue_timezone:
        IANA timezone string associated with the venue
        (e.g. ``"America/Mexico_City"``).

    Returns
    -------
    str
        Local time at the venue, formatted as ``HH:MM``.
    """
    return utc_to_local(utc_dt, venue_timezone)


def convert_datetime(
    utc_dt: datetime,
    target_tz: str,
    fmt: Optional[str] = None,
) -> datetime:
    """Convert a UTC ``datetime`` to a full ``datetime`` in *target_tz*.

    Returns a timezone-aware ``datetime`` object instead of a formatted string,
    giving callers full control over subsequent formatting.

    Parameters
    ----------
    utc_dt:
        Source UTC datetime (naive datetimes are treated as UTC).
    target_tz:
        IANA timezone name.
    fmt:
        If provided, return a formatted string instead of a ``datetime``.

    Returns
    -------
    datetime | str
        The converted datetime (or formatted string when *fmt* is given).
    """
    aware_utc = utc_dt.replace(tzinfo=ZoneInfo("UTC"))
    local_dt = aware_utc.astimezone(ZoneInfo(target_tz))
    if fmt is not None:
        return local_dt.strftime(fmt)
    return local_dt
