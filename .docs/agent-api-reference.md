# Agent API Reference

> Backend API contracts. Full spec is in `football-web/REQUIREMENTS.md` section VII.

## Status: APP FACTORY + DI + UTILS + SEED DATA + FRONTEND API CLIENT + REDIS INFRASTRUCTURE + CHEER SERVICE + LIVE SERVICE + WEBSOCKET + AI SERVICE + AI CONTROLLER + SCRAPER INFRASTRUCTURE + LIVE SCRAPER + DATA SYNC + SCHEDULER COMPLETE

Backend scaffold, exception hierarchy, middleware, ORM models, Pydantic schemas, repositories, services, controllers, **app factory (main.py)**, **dependency injection (dependencies.py)**, **run.py entry point**, **utility modules (utils/)**, **seed data pipeline**, **frontend API client layer**, **Redis infrastructure (app/redis/)**, **Cheer voting service/controller**, **Live Service**, **WebSocket manager + controller**, **AI Service (Deepseek API client with SSE streaming)**, **AI Controller (POST /api/ai/chat SSE endpoint)**, **Scraper infrastructure (BaseScraper + FIFAScraper)**, **Live Score Scraper (LiveScoreScraper)**, **Data Sync Service (DataSyncService)**, and **Scraper Scheduler (ScraperScheduler)** are implemented.
`uvicorn app.main:app --reload` starts successfully; `/docs` shows OpenAPI with all registered routes.
Seed data: `python -m scripts.seed_data` — one-click init (16 venues, 48 teams, 104 matches, bracket linkage, 48 group standings).
Frontend API client: `football-web/lib/api-client.ts` + `football-web/lib/api/*.ts` — typed fetch wrapper with `ApiResponse<T>` unwrapping, language headers, timeout, and unified error handling.
Redis: `app/redis/` — connection pool manager with graceful degradation (REDIS_ENABLED=false → all ops use fallbacks), key patterns via `RedisKeys` class.
Cheer: `app/services/cheer_service.py` + `app/controllers/cheer_controller.py` — Redis HASH atomic counters with in-memory fallback, IP-based rate limiting.
Live: `app/services/live_service.py` — Redis HASH real-time match state (status/score/activity) with in-memory fallback; `MatchService` auto-merges Redis live data into DB query results; **broadcasts WebSocket events** on state changes (score_update, match_start, match_end, activity_update, bracket_update).
WebSocket: `app/services/websocket_manager.py` + `app/controllers/ws_controller.py` — ConnectionManager singleton with connect/disconnect, subscribe/unsubscribe, broadcast/broadcast_to_match; WS /ws/live endpoint with initial payload, keep-alive pings, and auto-cleanup.

## Utility Layer

Shared helpers with no business-logic coupling, located in `app/utils/`.

| Module | Functions/Classes | Notes |
|--------|-------------------|-------|
| `markdown_parser.py` | `MarkdownParser`, `ParsedMatch` | Parses `data/2026_FIFA_World_Cup_Group_Stage.md` → 72 structured `ParsedMatch` objects (12 groups × 6 matches). Extracts: group_label, round_num, match_date, home/away team names (Chinese), FIFA rankings. |
| `timezone.py` | `utc_to_local(utc_dt, target_tz)`, `get_host_city_time(utc_dt, venue_tz)`, `convert_datetime(utc_dt, target_tz, fmt)` | Pure `zoneinfo`-based timezone conversion (no third-party deps). Used by MatchService, GroupService, BracketService. |

**ParsedMatch dataclass fields**: `group_label` (A-L), `round_num` (1-3), `match_date` (date), `home_team_zh`, `away_team_zh`, `fifa_ranking_home`, `fifa_ranking_away`

## Scraper Infrastructure (`app/scraping/`)

### `app/scraping/base_scraper.py` — BaseScraper
- **Rate limiting**: `asyncio.Semaphore` limits concurrent HTTP requests to `SCRAPER_CONCURRENCY` (default 3).
- **Retry with exponential backoff**: Up to `SCRAPER_RETRY_MAX` (default 3) retries with `2**attempt` second delays for transient failures.
- **Error hierarchy**: `ScraperError` (base) → `ScraperTimeoutError`, `ScraperHTTPError` (with `status_code`), `ScraperParseError`.
- **Retryable check**: Retries on `httpx.TimeoutException`, `httpx.ConnectError`, and HTTP 5xx. Non-retryable errors (4xx) raise immediately.
- **Structured logging**: Each request logs URL, status code, elapsed time, and attempt number.
- **HTTP client**: Uses `httpx.AsyncClient` with lazy init; supports async context-manager protocol.
- **Config**: `SCRAPER_CONCURRENCY`, `SCRAPER_TIMEOUT`, `SCRAPER_RETRY_MAX` from `app.config.settings`.

### `app/scraping/fifa_scraper.py` — FIFAScraper(BaseScraper)
- `scrape_match_schedule()` → `ScrapedSchedule` — Fetches FIFA schedule page, extracts `__NEXT_DATA__` JSON, parses match list.
- `scrape_match_result(match_id)` → `ScrapedMatchResult` — Fetches individual match page, extracts result with events.
- **JSON extraction**: `_extract_next_data()` regex extracts `__NEXT_DATA__` script tag content; multiple fallback JSON paths tried.
- **Graceful degradation**: Returns empty schedules/results when page structure doesn't match expectations.
- **Config**: `FIFA_SCHEDULE_URL`, `FIFA_MATCH_URL` from `app.config.settings`.

### `app/schemas/scraper_schema.py` — Scraper Data Models
| Model | Fields | Validation |
|-------|--------|------------|
| `ScrapedMatch` | external_id, home_team, away_team, kickoff_utc, stage, group_label?, venue_name?, status, home_score?, away_score? | stage ∈ {group, R32, R16, QF, SF, 3rd, F}; status ∈ {upcoming, live, finished, postponed} |
| `ScrapedSchedule` | matches: List[ScrapedMatch], scraped_at, source_url | — |
| `ScrapedLiveEvent` | event_type, minute (≥0), team_side, player_name? | team_side ∈ {home, away} |
| `ScrapedLiveScore` | match_id, home_score (≥0), away_score (≥0), status, activity_level (0-100), events: List[ScrapedLiveEvent] | status ∈ {upcoming, live, finished, postponed} |
| `ScrapedLiveScoreBatch` | matches: List[ScrapedLiveScore], scraped_at, source_url | — |
| `ScrapedEvent` | event_type, minute (≥0), team_side, player_name? | team_side ∈ {home, away} |
| `ScrapedMatchResult` | external_id, status, home_score (≥0), away_score (≥0), events, scraped_at, source_url | status ∈ {upcoming, live, finished, postponed} |

### `app/scraping/live_score_scraper.py` — LiveScoreScraper(BaseScraper)
- `scrape_live_scores()` → `ScrapedLiveScoreBatch` — Fetches schedule page, filters live matches, returns validated live score data with activity levels.
- **Activity level estimation**: `_estimate_activity_level(events, current_minute)` — heuristic based on event type weights and match minute progress.
- **Live status detection**: Accepts "live", "in_play", "inplay", "halftime", "1h", "2h", "et", "ht".
- Reuses `_extract_next_data()` from `fifa_scraper.py`.

### `app/scraping/data_sync.py` — DataSyncService
- `sync_live_scores(batch)` → int — Syncs live scores to Redis via `LiveService`. Returns count of matches synced.
- `sync_match_result(result)` → Optional[Match] — Syncs finished match result to SQLite (updates scores, status, events). Updates `LiveService` to reflect finished state.
- `sync_group_standings()` → int — Recalculates all 12 group standings from finished group matches. Returns count of rows updated.
- **Distributed lock**: `_acquire_lock()` / `_release_lock()` — Redis `SET NX EX` with Lua-script safe release (only deletes own token). Fallback to `asyncio.Lock` when Redis unavailable.
- **Lock key**: `RedisKeys.SCRAPER_LOCK` (= `scraper:lock`), TTL: 60s.
- **External ID resolution**: `_resolve_match_id()` queries DB first, falls back to integer parsing.

### `app/scraping/scheduler.py` — ScraperScheduler
- `start()` → None — Starts three `asyncio.Task` periodic loops. No-op when `SCRAPER_ENABLED=false`.
- `stop()` → None — Cancels all tasks via `task.cancel()`, awaits via `asyncio.gather(return_exceptions=True)`, logs non-CancelledError exceptions.
- **Periodic tasks**:
  - `live_scores` (default 30s, configurable via `SCRAPER_LIVE_INTERVAL`) — Scrapes live match data via `LiveScoreScraper`, syncs to Redis via `DataSyncService`. Skipped when no matches are currently live (checked via `LiveService.get_live_matches()`).
  - `finished_results` (default 5min, configurable via `SCRAPER_FINISHED_INTERVAL`) — Queries recent finished matches from DB, scrapes each result via `FIFAScraper`, persists scores/events via `DataSyncService.sync_match_result()`. 2s delay between individual scrapes.
  - `group_standings` (default 1h, configurable via `SCRAPER_GROUP_INTERVAL`) — Recalculates all 12 group standings via `DataSyncService.sync_group_standings()`.
- **Integration**: Started in `main.py` lifespan after DB engine + Redis init. Receives `sessionmaker` factory for per-task DB sessions.
- **Error handling**: Each periodic run catches all exceptions, logs via `logging.error`, and retries on next interval. `CancelledError` propagates for clean shutdown.
- **Configuration**: Intervals read from `app.config.settings` (env-overridable): `SCRAPER_LIVE_INTERVAL`, `SCRAPER_FINISHED_INTERVAL`, `SCRAPER_GROUP_INTERVAL`.

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
| `MatchService` | `get_match_dates()`, `get_matches(params, timezone_name, lang, page, page_size)`, `get_match_by_id(match_id, timezone_name, lang)`, `get_live_matches(timezone_name, lang)` | Multi-filter support (date/stage/group/team/status) with secondary in-memory filtering; timezone conversion via `zoneinfo` adds `local_time` and `host_time` fields; `get_match_dates` returns distinct dates with primary stage label; **auto-merges Redis live data** (status/score/activity_level) into query results when Redis is available |
| `GroupService` | `get_all_groups(lang)`, `get_group_detail(group_label, timezone_name, lang)` | Returns all 12 groups standings overview or single group detail with standings + matches; standings sorted by points desc, GD desc, GF desc; lang-aware (promotes `name_zh`); validates group label A-L |
| `BracketService` | `get_full_bracket(lang, timezone_name)`, `get_bracket_by_round(round_name, lang, timezone_name)`, `get_predictions()` | Returns knockout bracket tree (R32→R16→QF→SF→3rd→F) grouped by round; single round query; TBD teams in R32 matches carry `from_group`/`from_position` context (e.g. "1st Group A"); predictions endpoint returns placeholder for Phase 3 AI integration |
| `CheerService` | `get_cheers(match_id)`, `vote_cheer(match_id, side, client_ip)` | Redis HASH counters (`cheers:match:{id}` with `home`/`away` fields); HINCRBY atomic increment via pipeline; IP-based rate limiting (5-min cooldown per match+IP); in-memory class-level fallback when Redis unavailable; `_cleanup_expired_rate_limits()` prevents unbounded memory growth |
| `LiveService` | `update_match_status(match_id, status)`, `update_score(match_id, home_score, away_score)`, `update_activity(match_id, level)`, `get_live_matches()`, `get_match_live_data(match_id)`, `apply_sync_data(match_id, *, home_score?, away_score?, status?, activity_level?, events?)` | Redis HASH live state (`live:match:{id}` with `status`/`home_score`/`away_score`/`activity` fields); in-memory fallback; cache invalidation markers on status/score change; MatchService auto-merges Redis live data into query results via `_merge_live_data_batch()`; **broadcasts WebSocket events** on state changes (MATCH_START/MATCH_END/SCORE_UPDATE/ACTIVITY_UPDATE/BRACKET_UPDATE); `apply_sync_data()` is a batched update for DataSyncService with single Redis write+read cycle |
| `ConnectionManager` | `connect(websocket, client_id)`, `disconnect(client_id)`, `subscribe(client_id, match_id)`, `unsubscribe(client_id, match_id)`, `broadcast(event_type, data)`, `broadcast_to_match(match_id, event_type, data)`, `get_active_count()` | Module-level singleton via `get_manager()`; in-process registry of active WebSocket connections; asyncio.Lock-guarded state; auto-removes broken connections; supports per-match subscription channels |
| `AIService` | `stream_chat(messages, *, context, lang) -> AsyncGenerator[SSEEvent]`, `close()` | Deepseek API client (OpenAI-compatible `/chat/completions`, model=`deepseek-reasoner`); yields `SSEEvent` objects: `thinking` (reasoning delta), `answer` (content delta), `analysis` (structured JSON when analysis keywords detected), `done`, `error`; uses `httpx.AsyncClient` with lazy init; 30s timeout; graceful error handling (rate limit 429, timeout, generic errors → error events, never raises); no DB dependency; config from `settings.DEEPSEEK_API_KEY` / `settings.DEEPSEEK_BASE_URL` |

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
| `cheer_controller` | `GET /api/cheers/{match_id}` | — |
| `cheer_controller` | `POST /api/cheers/{match_id}` | Body: `{side: "home" \| "away"}`; IP-based rate limiting via `X-Forwarded-For` |
| `ws_controller` | `WS /ws/live` | WebSocket: initial payload (connected + live_matches), subscribe/unsubscribe by matchId, 30s ping keep-alive, auto-cleanup on disconnect |
| `ai_controller` | `POST /api/ai/chat` | Body: `ChatRequest` (`messages`, `context?`, `lang`); SSE streaming response; events: `thinking`, `answer`, `analysis`, `done`, `error`; terminated with `data: [DONE]\n\n` |

> Dependency injection is centralised in `app/dependencies.py`:
> - `get_db` — yields `AsyncSession` with auto-commit/rollback
> - `get_language` — extracts lang from query param or `Accept-Language` header
> - `get_team_service`, `get_match_service`, `get_venue_service`, `get_group_service`, `get_bracket_service`, `get_ai_service` — service factory functions
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
    └── /live                    # WebSocket real-time events (IMPLEMENTED)
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

### AI Chat (SSE Stream) — IMPLEMENTED
```
POST /api/ai/chat
Body: { messages: Array<{role, content}>, context?: {currentView, selectedDate, timezone}, lang: "zh-CN" | "en-US" }
Response: SSE stream (text/event-stream)
  data: {"type": "thinking", "content": "..."}    # Reasoning delta
  data: {"type": "answer", "content": "..."}       # Content delta
  data: {"type": "analysis", "data": {...}}        # Structured team analysis
  data: {"type": "error", "content": "..."}        # Error message
  data: {"type": "done"}                           # Stream complete
  data: [DONE]                                     # Terminal sentinel
```

### WebSocket Events
| Event | Data |
|-------|------|
| `score_update` | `{matchId, team, score, event}` |
| `match_start` | `{matchId, status}` |
| `match_end` | `{matchId, status, score}` |
| `activity_update` | `{matchId, activityLevel}` |
| `bracket_update` | `{matchId, winner, nextMatchId}` |
