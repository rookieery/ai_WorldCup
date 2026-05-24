"""API route (Controller) layer."""

from app.controllers.group_controller import router as group_router
from app.controllers.match_controller import router as match_router
from app.controllers.team_controller import router as team_router
from app.controllers.venue_controller import router as venue_router

__all__ = [
    "group_router",
    "match_router",
    "team_router",
    "venue_router",
]
