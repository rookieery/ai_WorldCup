# Services Layer — Agent Notes

## Architecture
- All services receive an `AsyncSession` at construction; callers manage the session lifecycle.
- Services delegate to repositories and return plain dicts (validated through Pydantic VOs).
- No direct ORM objects are returned — always convert to VO dicts via `model_validate().model_dump()`.

## Service Methods

### TeamService
- `get_all_teams(page, page_size, group, lang)` → `(items_vo, total)`
- `get_team_by_code(code, lang)` → `dict` (raises `NotFoundError`)
- `get_teams_by_group(group_label, lang)` → `list[dict]`
- `get_team_stats(code, lang, timezone_name)` → `dict` — comprehensive stats (team info, group standing, finished/upcoming matches); raises `NotFoundError`

### VenueService
- `get_all_venues(page, page_size)` → `(items_vo, total)`

### MatchService
- `get_matches(params, timezone_name, lang, page, page_size)` → `(items_vo, total)` — multi-filter with secondary in-memory filtering; **auto-merges Redis live data** when available
- `get_match_by_id(match_id, timezone_name, lang)` → `dict` (raises `NotFoundError`); **auto-merges Redis live data** when available
- `get_live_matches(timezone_name, lang)` → `list[dict]` — **auto-merges Redis live data** when available
- Constructor accepts optional `redis: Optional[Redis]` — injected via `get_match_service` DI which passes `get_redis()`
- Redis live data overrides: `status`, `home_score`, `away_score`, `activity_level` (from Redis `activity` field)
- `_merge_live_data_batch(items_vo)` — batch pipeline for multiple matches; `_get_live_data_from_redis(match_id)` — single match fetch

### GroupService
- `get_all_groups(lang)` → `list[dict]` — iterates A-L, returns each group with standings
- `get_group_detail(group_label, timezone_name, lang)` → `dict` — standings + matches; validates A-L

### BracketService
- `get_full_bracket(lang, timezone_name)` → `dict` — full knockout tree (R32→R16→QF→SF→3rd→F), grouped by round, sorted by position
- `get_bracket_by_round(round_name, lang, timezone_name)` → `dict` — single round query; validates round name
- `get_predictions()` → `dict` — returns TBD placeholder; Phase 3 AI integration
- Uses `MatchRepository.get_bracket_matches()` for data access
- TBD teams detected by code starting with "TBD"; from_group/from_position context ready for P1-16 populate
- Supports en/zh lang and timezone conversion like other services

### CheerService
- `get_cheers(match_id)` → `CheerResponse` — returns `{match_id, home, away}` counts from Redis HASH or in-memory fallback
- `vote_cheer(match_id, side, client_ip)` → `CheerResponse` — atomic HINCRBY increment via Redis pipeline, returns updated counts
- IP-based rate limiting: 5-min cooldown per (match_id, client_ip); raises `BusinessError` on duplicate
- Redis key: `cheers:match:{match_id}` (HASH with `home`/`away` fields)
- Rate-limit key: `cheer:ratelimit:{match_id}:{ip}` (Redis: string with TTL; memory: monotonic timestamp)
- Class-level `_shared_counts` / `_shared_rate_limits` dicts persist across per-request instances
- `_cleanup_expired_rate_limits()` classmethod removes stale memory entries
- No DB dependency — pure Redis/in-memory counter service

### LiveService
- `update_match_status(match_id, status)` → `dict` — updates match status in Redis HASH `live:match:{match_id}`; validates status ∈ {upcoming, live, finished, postponed}
- `update_score(match_id, home_score, away_score)` → `dict` — updates home/away scores; rejects negative values
- `update_activity(match_id, level)` → `dict` — updates activity level (clamped to 0-100)
- `get_live_matches()` → `list[dict]` — returns all matches with status=live from Redis (scan_iter) or memory
- `get_match_live_data(match_id)` → `dict | None` — returns single match live data or None if absent
- `apply_sync_data(match_id, *, home_score, away_score, status, activity_level, events)` → `dict` — batched update from DataSyncService; single Redis pipeline write+read; broadcasts WS events for status/score/activity changes
- Cache invalidation: `update_match_status` and `update_score` set TTL-based markers on `cache:groups` and `cache:bracket`
- In-memory fallback: module-level `_memory_store` dict (single-process dev only)
- Constructor: `LiveService(redis: Optional[Redis] = None)` — same pattern as CheerService
- No DB dependency — pure Redis/in-memory state service

### AIService
- `stream_chat(messages, *, context, lang) -> AsyncGenerator[SSEEvent]` — calls Deepseek API (OpenAI-compatible `/chat/completions`), streams SSE, yields `SSEEvent` objects
- Event types yielded: `thinking` (reasoning delta), `answer` (content delta), `analysis` (structured JSON when analysis keywords detected), `done`, `error`
- Uses `httpx.AsyncClient` with lazy init via `_get_client()`; 30s timeout
- Error handling: 429 rate limit → friendly error; timeout → error event; other exceptions → generic error (never raises, always yields error SSEEvent)
- No API key → yields `error` event immediately with "no_key" message
- Analysis detection: checks user message for analysis keywords (bilingual zh-CN/en-US); if detected, buffers answer and attempts JSON extraction post-stream
- `_extract_analysis_from_answer()` searches for embedded JSON with `team_code` key
- Model: `deepseek-reasoner` (supports `reasoning_content` delta field)
- No DB dependency — pure HTTP client service
- DI: `get_ai_service()` in `app/dependencies.py` — no DB session needed
- Config: reads `DEEPSEEK_API_KEY` and `DEEPSEEK_BASE_URL` from `app.config.settings`

## Language Handling Pattern
- All services accept `lang="en"` (default) or `lang="zh"`.
- When `lang == "zh"`, the helper `_apply_team_lang()` promotes `name_zh` into the `name` field.
- This pattern is duplicated across services; a shared utility module would be a future refactor target.

## Timezone Conversion
- All services now use the shared `app.utils.timezone` module instead of local duplicates.
- `utc_to_local(utc_dt, target_tz)` → `"HH:MM"` string, `get_host_city_time(utc_dt, venue_tz)` → `"HH:MM"` string.
- `convert_datetime(utc_dt, target_tz, fmt)` → full `datetime` or formatted string.
- `local_time` = user's requested timezone, `host_time` = venue's timezone.
- Uses `zoneinfo` standard library — no extra dependencies (except `tzdata` on Windows, added to pyproject.toml).
