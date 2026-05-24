# Business Overview — World Cup 2026 Dashboard

## Product Summary

Real-time FIFA World Cup 2026 dashboard for global football fans. Features match schedules, live scores, knockout bracket visualization, and AI-powered match analysis chatbot.

**Visual Style**: Cyberpunk dark glassmorphism (Midnight Navy + Electric Lime/Cyan/Magenta accents).

## Current State

| Aspect | Status |
|--------|--------|
| Frontend UI | Complete visual shell (all components built) |
| Data Source | 100% hardcoded in components |
| Backend API | Scaffold + exceptions + middleware + ORM models (5 tables) + Pydantic schemas (8 modules) + Alembic migrations |
| State Management | Local `useState` only, no global store |
| Routing | Single `/` route, no navigation |
| AI Service | Simulated (2s timeout, fixed response) |
| Real-time Updates | None (WebSocket not implemented) |

## Core Business Entities

### Match
- Identified by `id` (number)
- Has two `Team` objects, stage, status, scores, times, venue
- Status flow: `upcoming` → `live` → `finished`
- Special flags: `isBigMatch`, `activityLevel` (0–100)

### Team
- Identified by 3-letter code (`BRA`, `FRA`, etc.)
- Properties: name, code, flag (emoji), FIFA ranking

### Bracket Match
- Identified by string `id` (`"qf1"`, `"sf1"`, `"f1"`)
- Round types: `QF`, `SF`, `F` (needs expansion: `R32`, `R16`, `3rd`)
- Links to next match via `nextMatchId` (defined in REQUIREMENTS but not yet in code)

### Team Analysis (AI)
- 5-dimension radar: attack, defense, possession, setpieces, form (0–100 each)
- Win/draw probabilities, key insights list

## Data Flow (Current)

```
page.tsx (state owner)
├── timezone ──────→ Header (toggle display)
├── viewMode ──────→ Header (toggle) → switches Timeline/Bracket
├── selectedDate ──→ DateTimeline (highlight) → MatchCardsGrid (passed but unused)
│
├── [Timeline Mode]
│   ├── DateTimeline ──── hardcoded 40-day array
│   └── MatchCardsGrid ── hardcoded 4-match array
│
├── [Bracket Mode]
│   └── TournamentBracket ── hardcoded 7-match array (QF+SF+F)
│
└── AICopilotPanel ──── hardcoded messages + 2s fake response
```

## Data Flow (Target — from REQUIREMENTS.md)

```
page.tsx (state owner)
├── [State Store: Zustand]
│   ├── user preferences (timezone, view mode, theme)
│   ├── match data cache (from API)
│   ├── live updates (from WebSocket)
│   └── AI chat history
│
├── [API Layer]
│   ├── GET /api/matches?date=... → match list
│   ├── GET /api/bracket → full knockout tree
│   ├── GET /api/groups/:group → standings
│   ├── POST /api/ai/chat → streaming AI response
│   ├── GET /api/cheers/:matchId → fan vote data
│   └── WS /api/ws/live → real-time score updates
│
└── [Routes]
    ├── / → Dashboard (Timeline/Bracket)
    ├── /groups → Group standings
    ├── /groups/:group → Single group detail
    ├── /matches/:id → Match detail
    ├── /teams/:code → Team detail
    ├── /bracket → Full bracket (standalone)
    └── /stats → Statistics center
```

## Tournament Structure (2026 World Cup)

| Phase | Details |
|-------|---------|
| Groups | 12 groups (A–L), 4 teams each |
| Group Stage | 72 matches (6 per group) |
| Qualification | Top 2 per group + 8 best 3rd-place = 32 teams |
| Knockout R32 | 16 matches |
| Knockout R16 | 8 matches |
| Quarter-Finals | 4 matches |
| Semi-Finals | 2 matches |
| 3rd Place | 1 match |
| Final | 1 match |
| **Total** | **104 matches** |

## Backend Architecture (Implemented)

### Exception Hierarchy
```
AppException (base, code=500)
├── NotFoundError (code=404)
├── ValidationError (code=422)
├── BusinessError (code=400)
└── ExternalServiceError (code=502)
```

### Middleware Stack
- **ErrorHandlerMiddleware**: Catches all exceptions → unified `{code, data, message}` JSON response
- **CORS Middleware**: Origins from `settings.CORS_ORIGINS` (env-configurable)
- **LoggingMiddleware**: Logs `method path → status (duration_ms)` for every request

### Unified API Response Format
All API responses (success and error) follow: `{"code": int, "data": T | null, "message": str}`

### ORM Models (SQLAlchemy 2.0 Declarative)
```
Base (DeclarativeBase)
└── TimestampMixin (created_at, updated_at)
    ├── Team (id, name UNIQUE, name_zh, code UNIQUE, flag, fifa_ranking, group_label, confederation, world_cup_appearances)
    ├── Venue (id, name, city, country, timezone, utc_offset, capacity)
    ├── Match (id, external_id UNIQUE, home/away_team_id FK→Team, venue_id FK→Venue, stage, group_label, round, match_day, kickoff_utc, status, home/away_score, is_big_match, activity_level, next_match_id FK→Match(self), position)
    ├── GroupStanding (id, team_id FK UNIQUE→Team, group_label, played, won, drawn, lost, goals_for, goals_against, goal_difference, points, position)
    └── MatchEvent (id, match_id FK→Match, event_type, minute, team_side, player_name)

Relationships:
  Team 1:N Match (home_matches, away_matches)
  Team 1:1 GroupStanding (standing)
  Venue 1:N Match (matches)
  Match 1:N MatchEvent (events, cascade delete)
  Match self-ref next_match (bracket linkage)
```

### Pydantic Schemas (Request/Response Validation)
```
common.py
├── ApiResponse[T]           # {code: int, data: T | null, message: str}
└── PaginatedResponse[T]     # {items: List[T], total, page, page_size}

team_schema.py
├── TeamCreate (DTO)         # name, name_zh, code, flag, fifa_ranking, group_label, confederation, world_cup_appearances
├── TeamUpdate (DTO)         # All fields optional
├── TeamResponse (VO)        # Full team data
└── TeamListResponse (VO)    # Minimal team data for lists/dropdowns

match_schema.py
├── MatchQueryParams (DTO)   # date, stage, group, team, status filters
├── MatchEventResponse (VO)  # event_type, minute, team_side, player_name
├── MatchResponse (VO)       # Nested TeamListResponse + VenueResponse
└── MatchDetailResponse (VO) # Extends MatchResponse + events list

venue_schema.py
└── VenueResponse (VO)       # name, city, country, timezone, utc_offset, capacity

group_schema.py
├── GroupStandingResponse (VO) # team + stats (played/won/drawn/lost/GF/GA/GD/pts/pos)
└── GroupDetailResponse (VO)   # group_label + standings + matches

bracket_schema.py
├── BracketTeamResponse (VO)   # Team slot (supports TBD with from_group/from_position)
├── BracketMatchResponse (VO)  # home/away BracketTeam + stage + status
├── BracketRoundResponse (VO)  # round_name + matches list
└── BracketTreeResponse (VO)   # rounds list (full knockout tree)

cheer_schema.py
├── CheerVoteRequest (DTO)   # side: "home" | "away"
└── CheerResponse (VO)       # match_id, home count, away count

ai_schema.py
├── ChatRequest (DTO)        # messages + context + lang
├── SSEEvent (VO)            # type: thinking/answer/analysis/done/error + content/data
└── TeamAnalysisResponse (VO) # radar dimensions + win_probability + insights

ws_schema.py
├── WSEventType (Enum)       # score_update, match_start, match_end, activity_update, cheer_update, bracket_update
└── WSMessage (VO)           # event + payload dict
```

All response models use `from_attributes = True` for seamless ORM → VO conversion.

### Database Migrations (Alembic)
- **Config**: `alembic.ini` + `alembic/env.py` (async mode via aiosqlite)
- **DB URL**: Dynamically resolved from `app.config.settings.DATABASE_URL`
- **Batch mode**: `render_as_batch=True` for SQLite ALTER TABLE support
- **Initial migration** (`001_initial_schema.py`): Creates teams, venues, group_standings, matches, match_events with all FK constraints
- **Commands**: `alembic upgrade head` / `alembic downgrade base`

## Key Implementation Gaps

1. **No API integration** — all data hardcoded (schemas layer ready)
2. **No global state** — Zustand recommended
3. **No routing** — single page only
4. **Bracket incomplete** — only QF→SF→F, needs R32→R16→QF→SF→3rd→F
5. **Types not shared** — duplicated across components
6. **Date filtering missing** — `selectedDate` passed but not used
7. **Group standings missing** — entire UI section not built
8. **Match detail missing** — no click-to-view match info
9. **AI is fake** — simulated responses, no backend
10. **No real-time updates** — no WebSocket/SSE

## AI Prediction Skills

Two skill files define the reasoning framework for match predictions:

- `skills/group_stage_predict.md` — 6-step reasoning (form, H2H, tactics, key players, home advantage, intangibles)
- `skills/knockout_stage_predict.md` — 5-step reasoning (form, H2H, knockout psychology, tactical matchup, X-factors)

These should power the backend AI service (`POST /api/ai/chat`).
