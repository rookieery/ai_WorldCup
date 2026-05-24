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

### VenueService
- `get_all_venues(page, page_size)` → `(items_vo, total)`

### MatchService
- `get_matches(params, timezone_name, lang, page, page_size)` → `(items_vo, total)` — multi-filter with secondary in-memory filtering
- `get_match_by_id(match_id, timezone_name, lang)` → `dict` (raises `NotFoundError`)
- `get_live_matches(timezone_name, lang)` → `list[dict]`

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
