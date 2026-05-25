"""API route (Controller) layer."""

from app.controllers.ai_controller import router as ai_router
from app.controllers.bracket_controller import router as bracket_router
from app.controllers.cheer_controller import router as cheer_router
from app.controllers.group_controller import router as group_router
from app.controllers.match_controller import router as match_router
from app.controllers.team_controller import router as team_router
from app.controllers.venue_controller import router as venue_router
from app.controllers.ws_controller import router as ws_router

__all__ = [
    "ai_router",
    "bracket_router",
    "cheer_router",
    "group_router",
    "match_router",
    "team_router",
    "venue_router",
    "ws_router",
]
