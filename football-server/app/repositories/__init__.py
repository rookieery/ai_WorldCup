"""Data-access (Repository) layer — generic CRUD base + entity-specific repos."""

from app.repositories.base import BaseRepository
from app.repositories.team_repo import TeamRepository
from app.repositories.match_repo import MatchRepository
from app.repositories.venue_repo import VenueRepository
from app.repositories.group_repo import GroupRepository
from app.repositories.match_event_repo import MatchEventRepository

__all__ = [
    "BaseRepository",
    "TeamRepository",
    "MatchRepository",
    "VenueRepository",
    "GroupRepository",
    "MatchEventRepository",
]