"""Centralised Redis key pattern definitions.

All key patterns used across the application are declared here so that
every module references keys by symbolic name rather than raw strings.

Usage::

    from app.redis.keys import RedisKeys

    key = RedisKeys.LIVE_MATCH.format(match_id=42)
"""

from __future__ import annotations


class RedisKeys:
    """Namespace class holding format-string key templates."""

    # ── Live match data ───────────────────────────────────────────────────
    # Hash fields: status, home_score, away_score, activity
    LIVE_MATCH: str = "live:match:{match_id}"

    # ── Fan cheer counts ──────────────────────────────────────────────────
    # Hash fields: home, away
    CHEERS_MATCH: str = "cheers:match:{match_id}"

    # ── WebSocket connection tracking ─────────────────────────────────────
    # Set of active client IDs
    WS_CONNECTIONS: str = "ws:connections"

    # ── Cache invalidation markers ────────────────────────────────────────
    # String value — group standings JSON cache
    CACHE_GROUPS: str = "cache:groups"

    # String value — bracket tree JSON cache
    CACHE_BRACKET: str = "cache:bracket"

    # ── Scraper distributed lock ──────────────────────────────────────────
    # String value — lock token with TTL
    SCRAPER_LOCK: str = "scraper:lock"
