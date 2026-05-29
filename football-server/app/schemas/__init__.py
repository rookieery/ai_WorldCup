"""Pydantic schemas package — request DTOs and response VOs for all entities."""

from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.team_schema import (
    TeamCreate,
    TeamUpdate,
    TeamResponse,
    TeamListResponse,
)
from app.schemas.match_schema import (
    MatchQueryParams,
    MatchResponse,
    MatchDetailResponse,
    MatchEventResponse,
)
from app.schemas.venue_schema import VenueResponse
from app.schemas.group_schema import (
    GroupStandingResponse,
    GroupDetailResponse,
)
from app.schemas.bracket_schema import (
    BracketTeamResponse,
    BracketMatchResponse,
    BracketRoundResponse,
    BracketTreeResponse,
)
from app.schemas.cheer_schema import CheerResponse, CheerVoteRequest
from app.schemas.ai_schema import (
    ChatRequest,
    SSEEvent,
    TeamAnalysisResponse,
    TeamBrief,
    MatchEventBrief,
    MatchAnalysisRequest,
    SkillInfo,
)
from app.schemas.ws_schema import WSEventType, WSMessage
from app.schemas.scraper_schema import (
    ScrapedMatch,
    ScrapedSchedule,
    ScrapedEvent,
    ScrapedMatchResult,
)

__all__ = [
    # common
    "ApiResponse",
    "PaginatedResponse",
    # team
    "TeamCreate",
    "TeamUpdate",
    "TeamResponse",
    "TeamListResponse",
    # match
    "MatchQueryParams",
    "MatchResponse",
    "MatchDetailResponse",
    "MatchEventResponse",
    # venue
    "VenueResponse",
    # group
    "GroupStandingResponse",
    "GroupDetailResponse",
    # bracket
    "BracketTeamResponse",
    "BracketMatchResponse",
    "BracketRoundResponse",
    "BracketTreeResponse",
    # cheer
    "CheerResponse",
    "CheerVoteRequest",
    # ai
    "ChatRequest",
    "SSEEvent",
    "TeamAnalysisResponse",
    "TeamBrief",
    "MatchEventBrief",
    "MatchAnalysisRequest",
    "SkillInfo",
    # ws
    "WSEventType",
    "WSMessage",
    # scraper
    "ScrapedMatch",
    "ScrapedSchedule",
    "ScrapedEvent",
    "ScrapedMatchResult",
]
