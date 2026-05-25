# Controllers Layer — Agent Notes

## Architecture
- All controllers use FastAPI `APIRouter` with `Depends(get_*_service)` from `app/dependencies.py` for DI.
- All responses wrapped in `ApiResponse[T]` (unified `{code, data, message}` envelope).
- Service instances are injected via DI factory functions (no manual instantiation in routes).

## Dependency Injection
- Centralised in `app/dependencies.py`.
- Each controller uses `Depends(get_<domain>_service)` instead of manual `_get_db` + `Svc(session)`.
- Engine lifecycle managed by `app/main.py` lifespan (init on startup, dispose on shutdown).
- `get_db` provides auto-commit/rollback session management.
- `get_match_service` now injects optional `Redis` via `Depends(get_redis)` for live data merging.

## Registered Routes

### match_controller (`/api/matches`)
- `GET /api/matches` — multi-filter (date, stage, group, team, status) + pagination; **auto-merges Redis live data** (status/score/activity_level) when Redis available
- `GET /api/matches/live` — currently live matches; **auto-merges Redis live data** when available
- `GET /api/matches/{id}` — single match detail with events; **auto-merges Redis live data** when available

### team_controller (`/api/teams`)
- `GET /api/teams` — paginated team list, optional group filter
- `GET /api/teams/{code}/stats` — comprehensive team stats (standing + finished/upcoming matches)
- `GET /api/teams/{code}` — single team by 3-letter code

### venue_controller (`/api/venues`)
- `GET /api/venues` — paginated venue list with timezone info

### group_controller (`/api/groups`)
- `GET /api/groups` — all 12 groups with standings overview
- `GET /api/groups/{group}` — single group detail (A-L) with standings + matches

### bracket_controller (`/api/bracket`)
- `GET /api/bracket` — full knockout bracket tree (R32→R16→QF→SF→3rd→F), grouped by round
- `GET /api/bracket/predictions` — AI bracket predictions (returns TBD placeholder for Phase 3)

### cheer_controller (`/api/cheers`)
- `GET /api/cheers/{match_id}` — return current cheer counts `{home, away}` for a match
- `POST /api/cheers/{match_id}` — submit vote (body: `{side: "home" | "away"}`); IP-based rate limiting
- Uses `_get_cheer_service()` factory (no DB session needed; injects optional Redis client)
- Client IP extracted from `X-Forwarded-For` header or `request.client.host`

### ai_controller (`/api/ai`)
- `POST /api/ai/chat` — SSE streaming AI chat endpoint
- Accepts `ChatRequest` body: `{messages: [{role, content}], context?: ChatContext, lang: "zh-CN" | "en-US"}`
- Calls `PromptBuilder.build_system_prompt()` + `PromptBuilder.build_chat_context()` to assemble the full message list
- Delegates to `AIService.stream_chat()` which yields `SSEEvent` objects
- Returns `StreamingResponse` with `text/event-stream` content type
- Each event formatted as `data: {json}\n\n`, stream terminated with `data: [DONE]\n\n`
- SSE headers: `Cache-Control: no-cache`, `Connection: keep-alive`, `X-Accel-Buffering: no`
- Uses `Depends(get_ai_service)` — no DB session needed
- Event types: `thinking`, `answer`, `analysis`, `done`, `error`

## Common Query Params
- `lang`: `en` (default) or `zh` — controls name language
- `timezone`: IANA timezone string — adds `local_time` field to match data
- `page` / `page_size`: pagination (1-based, default 20)
