# Agent API Reference

> Backend API contracts. Full spec is in `football-web/REQUIREMENTS.md` section VII.

## Status: APP FACTORY + DI + UTILS + SEED DATA + FRONTEND API CLIENT + REDIS INFRASTRUCTURE COMPLETE

Backend scaffold, exception hierarchy, middleware, ORM models, Pydantic schemas, repositories, services, controllers, **app factory (main.py)**, **dependency injection (dependencies.py)**, **run.py entry point**, **utility modules (utils/)**, **seed data pipeline**, **frontend API client layer**, and **Redis infrastructure (app/redis/)** are implemented.
`uvicorn app.main:app --reload` starts successfully; `/docs` shows OpenAPI with all registered routes.
Seed data: `python -m scripts.seed_data` — one-click init (16 venues, 48 teams, 104 matches, bracket linkage, 48 group standings).
Frontend API client: `football-web/lib/api-client.ts` + `football-web/lib/api/*.ts` — typed fetch wrapper with `ApiResponse<T>` unwrapping, language headers, timeout, and unified error handling.
Redis: `app/redis/` — connection pool manager with graceful degradation (REDIS_ENABLED=false → all ops use fallbacks), key patterns via `RedisKeys` class.

Backend scaffold, exception hierarchy, middleware, ORM models, Pydantic schemas, repositories, services, controllers, **app factory (main.py)**, **dependency injection (dependencies.py)**, **run.py entry point**, **utility modules (utils/)**, and **seed data pipeline** are implemented.
`uvicorn app.main:app --reload` starts successfully; `/docs` shows OpenAPI with all registered routes.
Seed data: `python -m scripts.seed_data` — one-click init (16 venues, 48 teams, 104 matches, bracket linkage, 48 group standings).
Cheer services/controllers are not yet built.

## Utility Layer

Shared helpers with no business-logic coupling, located in `app/utils/`.

| Module | Functions/Classes | Notes |
|--------|-------------------|-------|
| `markdown_parser.py` | `MarkdownParser`, `ParsedMatch` | Parses `data/2026_FIFA_World_Cup_Group_Stage.md` → 72 structured `ParsedMatch` objects (12 groups × 6 matches). Extracts: group_label, round_num, match_date, home/away team names (Chinese), FIFA rankings. |
| `timezone.py` | `utc_to_local(utc_dt, target_tz)`, `get_host_city_time(utc_dt, venue_tz)`, `convert_datetime(utc_dt, target_tz, fmt)` | Pure `zoneinfo`-based timezone conversion (no third-party deps). Used by MatchService, GroupService, BracketService. |

**ParsedMatch dataclass fields**: `group_label` (A-L), `round_num` (1-3), `match_date` (date), `home_team_zh`, `away_team_zh`, `fifa_ranking_home`, `fifa_ranking_away`

## Redis Infrastructure (`app/redis/`)

### `app/redis/client.py` — Connection Pool Manager
- `init_redis_pool()` — Creates async connection pool via `redis.asyncio`; verifies with `ping()`. No-op when `REDIS_ENABLED=false`.
- `close_redis_pool()` — Graceful shutdown; closes both `Redis` and `ConnectionPool`.
- `get_redis() -> Optional[Redis]` — FastAPI `Depends` provider; returns `None` when Redis unavailable.
- `is_redis_available() -> bool` — Health-check for downstream services.
- Graceful degradation: connection failure logs warning, never blocks startup.

### `app/redis/keys.py` — Key Pattern Definitions
| Constant | Pattern | Purpose |
|----------|---------|---------|
| `LIVE_MATCH` | `live:match:{match_id}` | Real-time score/status/activity hash |
| `CHEERS_MATCH` | `cheers:match:{match_id}` | Fan cheer counts (home/away) hash |
| `WS_CONNECTIONS` | `ws:connections` | Active WebSocket client IDs set |
| `CACHE_GROUPS` | `cache:groups` | Group standings JSON cache |
| `CACHE_BRACKET` | `cache:bracket` | Bracket tree JSON cache |
| `SCRAPER_LOCK` | `scraper:lock` | Scraper distributed lock |

Usage: `RedisKeys.LIVE_MATCH.format(match_id=42)` → `"live:match:42"`

## Service Layer

All services receive an `AsyncSession` at construction; they delegate to repositories and return plain dicts (validated through Pydantic VOs).

| Service | Methods | Notes |
|---------|---------|-------|
| `TeamService` | `get_all_teams(page, page_size, group, lang)`, `get_team_by_code(code, lang)`, `get_teams_by_group(group_label, lang)` | Supports `lang="zh"` to promote `name_zh` into `name` field |
| `VenueService` | `get_all_venues(page, page_size)` | Returns venues with timezone info |
| `MatchService` | `get_match_dates()`, `get_matches(params, timezone_name, lang, page, page_size)`, `get_match_by_id(match_id, timezone_name, lang)`, `get_live_matches(timezone_name, lang)` | Multi-filter support (date/stage/group/team/status) with secondary in-memory filtering; timezone conversion via `zoneinfo` adds `local_time` and `host_time` fields; `get_match_dates` returns distinct dates with primary stage label |
| `GroupService` | `get_all_groups(lang)`, `get_group_detail(group_label, timezone_name, lang)` | Returns all 12 groups standings overview or single group detail with standings + matches; standings sorted by points desc, GD desc, GF desc; lang-aware (promotes `name_zh`); validates group label A-L |
| `BracketService` | `get_full_bracket(lang, timezone_name)`, `get_bracket_by_round(round_name, lang, timezone_name)`, `get_predictions()` | Returns knockout bracket tree (R32→R16→QF→SF→3rd→F) grouped by round; single round query; TBD teams in R32 matches carry `from_group`/`from_position` context (e.g. "1st Group A"); predictions endpoint returns placeholder for Phase 3 AI integration |

## Controller Layer

Controllers use FastAPI `APIRouter` with `Depends(get_*_service)` from `app/dependencies.py` for DI. All responses wrapped in `ApiResponse[T]`.

| Controller | Routes | Query Params |
|-----------|--------|-------------|
| `team_controller` | `GET /api/teams` | `page`, `page_size`, `group` (A-L), `lang` (en/zh) |
| `team_controller` | `GET /api/teams/{code}` | `lang` (en/zh) |
| `venue_controller` | `GET /api/venues` | `page`, `page_size` |
| `match_controller` | `GET /api/matches` | `date` (YYYY-MM-DD), `stage`, `group` (A-L), `team` (code), `status`, `timezone` (IANA), `lang`, `page`, `page_size` |
| `match_controller` | `GET /api/matches/dates` | — |
| `match_controller` | `GET /api/matches/live` | `timezone` (IANA), `lang` |
| `match_controller` | `GET /api/matches/{id}` | `timezone` (IANA), `lang` |
| `group_controller` | `GET /api/groups` | `lang` (en/zh) |
| `group_controller` | `GET /api/groups/{group}` | `timezone` (IANA), `lang` (en/zh) |
| `bracket_controller` | `GET /api/bracket` | `timezone` (IANA), `lang` (en/zh) |
| `bracket_controller` | `GET /api/bracket/predictions` | — |

> Dependency injection is centralised in `app/dependencies.py`:
> - `get_db` — yields `AsyncSession` with auto-commit/rollback
> - `get_language` — extracts lang from query param or `Accept-Language` header
> - `get_team_service`, `get_match_service`, `get_venue_service`, `get_group_service`, `get_bracket_service` — service factory functions
> - `get_redis` (from `app/redis/client.py`) — returns `Optional[Redis]` (`None` when Redis unavailable)
> Engine lifecycle managed by `main.py` lifespan (init on startup, dispose on shutdown).
> Redis pool lifecycle also managed by `main.py` lifespan (init_redis_pool on startup, close_redis_pool on shutdown).

## Repository Layer

All repos inherit from `BaseRepository[T]` (generic CRUD with pagination).
Each repo receives an `AsyncSession` at construction; callers control the session lifecycle.

| Repository | Extra Methods | Notes |
|-----------|---------------|-------|
| `TeamRepository` | `get_by_code(code)`, `get_by_group(group_label)` | Raises `NotFoundError` on missing code |
| `MatchRepository` | `get_by_date(date)`, `get_by_stage(stage)`, `get_by_status(status)`, `get_live_matches()`, `get_bracket_matches()`, `get_by_group_label(group)`, `get_by_team_code(code)`, `get_match_dates()` | All paginated except `get_live_matches` / `get_bracket_matches` / `get_match_dates` |
| `VenueRepository` | — (base CRUD only) | |
| `GroupRepository` | `get_by_group_label(group)` (sorted: pts desc, GD desc, GF desc), `get_group_matches(group)` | Returns both standings and matches for a group |
| `MatchEventRepository` | `get_by_match(match_id)` (sorted by minute asc) | |

**BaseRepository[T] methods**: `get_by_id`, `get_by_id_optional`, `get_all(page, page_size, filters, order_by)`, `create(data)`, `update(entity_id, data)`, `delete(entity_id)`

## Database Schema (5 tables)

All models use SQLAlchemy 2.0 `Mapped[]` type annotations with `mapped_column()`.

| Table | PK | Unique Columns | Foreign Keys |
|-------|----|---------------|--------------|
| `teams` | id | name, code | — |
| `venues` | id | — | — |
| `matches` | id | external_id | home_team_id→teams, away_team_id→teams, venue_id→venues, next_match_id→matches(self) |
| `group_standings` | id | team_id | team_id→teams |
| `match_events` | id | — | match_id→matches |

All tables include `TimestampMixin` columns: `created_at`, `updated_at` (auto-managed).

## Unified Response Envelope

All endpoints return responses wrapped in:

```json
{
  "code": 200,
  "data": <T | null>,
  "message": "success"
}
```

Error responses follow the same shape with appropriate HTTP status codes.
Exception mapping: `NotFoundError→404`, `ValidationError→422`, `BusinessError→400`, `ExternalServiceError→502`, unhandled→500.

## Planned API Structure

```
/api
├── /matches
│   ├── GET /                    # Match list (filter: date, stage, group, team, status)
│   ├── GET /dates               # All match dates with stage labels
│   ├── GET /:id                 # Single match detail
│   └── GET /live                # Current live matches
├── /bracket
│   ├── GET /                    # Full knockout bracket tree
│   └── GET /predictions         # AI bracket predictions
├── /teams
│   ├── GET /                    # All teams
│   ├── GET /:code               # Team detail
│   └── GET /:code/stats         # Team statistics
├── /groups
│   ├── GET /                    # All group standings
│   └── GET /:group              # Single group (standings + matches)
├── /venues
│   └── GET /                    # Venue list (with timezone info)
├── /cheers
│   ├── GET /:matchId            # Fan vote data for a match
│   └── POST /:matchId           # Submit fan vote
├── /ai
│   └── POST /chat               # AI chat (SSE streaming)
└── /ws
    └── /live                    # WebSocket real-time events
```

## Key Data Models (from REQUIREMENTS.md)

See `football-web/REQUIREMENTS.md` for full request/response examples and field definitions.

### Match Response Shape
```typescript
interface MatchResponse {
  date: string
  matches: Array<{
    id: number
    stage: string
    round: number
    status: "upcoming" | "live" | "finished"
    isBigMatch: boolean
    activityLevel: number
    team1: { name: string; code: string; flag: string; fifaRanking: number }
    team2: { name: string; code: string; flag: string; fifaRanking: number }
    score: { team1: number; team2: number } | null
    localTime: string
    hostTime: string
    venue: string
    hostCity: string
    hostCityTimezone: string
  }>
}
```

### Bracket Response Shape
```typescript
interface BracketResponse {
  rounds: Array<{
    name: string
    shortName: "R32" | "R16" | "QF" | "SF" | "3rd" | "F"
    matches: Array<{
      id: string
      position: number
      status: "upcoming" | "live" | "completed"
      team1: BracketTeam
      team2: BracketTeam
      nextMatchId: string
      venue: string
      matchTime: string
    }>
  }>
}
```

### AI Chat (SSE Stream)
```
POST /api/ai/chat
Body: { messages: Array<{role, content}>, context: {currentView, selectedDate, timezone} }
Response: SSE stream
  data: {"type": "text", "content": "..."}
  data: {"type": "analysis", "data": {TeamAnalysis}}
  data: {"type": "done"}
```

### WebSocket Events
| Event | Data |
|-------|------|
| `score_update` | `{matchId, team, score, event}` |
| `match_start` | `{matchId, status}` |
| `match_end` | `{matchId, status, score}` |
| `activity_update` | `{matchId, activityLevel}` |
| `bracket_update` | `{matchId, winner, nextMatchId}` |
