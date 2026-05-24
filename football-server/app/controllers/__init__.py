"""API route (Controller) layer."""

from app.controllers.team_controller import router as team_router
from app.controllers.venue_controller import router as venue_router

__all__ = [
    "team_router",
    "venue_router",
]
