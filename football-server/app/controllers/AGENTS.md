# Controllers Layer — Agent Notes

## Architecture
- All controllers use FastAPI `APIRouter` with `Depends(_get_db)` for session injection.
- All responses wrapped in `ApiResponse[T]` (unified `{code, data, message}` envelope).
- Service instances are created per-request inside the route handler.

## Session Helper
- Each controller has an inline `_get_db()` async generator.
- P1-11 will centralise this into `app/dependencies.py`.
- Pattern: create engine → sessionmaker → yield session → auto-close.

## Registered Routes

### match_controller (`/api/matches`)
- `GET /api/matches` — multi-filter (date, stage, group, team, status) + pagination
- `GET /api/matches/live` — currently live matches
- `GET /api/matches/{id}` — single match detail with events

### team_controller (`/api/teams`)
- `GET /api/teams` — paginated team list, optional group filter
- `GET /api/teams/{code}` — single team by 3-letter code

### venue_controller (`/api/venues`)
- `GET /api/venues` — paginated venue list with timezone info

### group_controller (`/api/groups`)
- `GET /api/groups` — all 12 groups with standings overview
- `GET /api/groups/{group}` — single group detail (A-L) with standings + matches

### bracket_controller (`/api/bracket`)
- `GET /api/bracket` — full knockout bracket tree (R32→R16→QF→SF→3rd→F), grouped by round
- `GET /api/bracket/predictions` — AI bracket predictions (returns TBD placeholder for Phase 3)

## Common Query Params
- `lang`: `en` (default) or `zh` — controls name language
- `timezone`: IANA timezone string — adds `local_time` field to match data
- `page` / `page_size`: pagination (1-based, default 20)
