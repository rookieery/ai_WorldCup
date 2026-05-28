# Utils — Agent Notes

## Architecture
- Shared utility modules with **no business-logic coupling** — no imports from services/controllers.
- All functions are pure and stateless, making them safe for concurrent use.

## markdown_parser.py
- `MarkdownParser(file_path=None, year=2026)` — parses group-stage markdown → `list[ParsedMatch]`.
- Default path: `data/2026_FIFA_World_Cup_Group_Stage.md` (resolved relative to repo root).
- Returns exactly **72** `ParsedMatch` objects (12 groups × 6 matches).
- Handles edge cases: FIFA ranking `-` for playoff qualifiers → `None`, Chinese date/month parsing.
- `ParsedMatch` is a frozen dataclass: `group_label`, `round_num`, `match_date`, `home_team_zh`, `away_team_zh`, `fifa_ranking_home`, `fifa_ranking_away`.

## timezone.py
- `utc_to_local(utc_dt, target_tz)` → `"HH:MM"` string. Naive datetimes treated as UTC.
- `get_host_city_time(utc_dt, venue_timezone)` → convenience wrapper for venue local time.
- `convert_datetime(utc_dt, target_tz, fmt=None)` → full `datetime` or formatted string.
- All functions use `zoneinfo.ZoneInfo` (Python 3.9+ stdlib). `tzdata` package needed on Windows.

## Consumers
- `app.services.match_service` — imports `utc_to_local` for `local_time` / `host_time` fields.
- `app.services.group_service` — imports `utc_to_local` for group match time fields.
- `app.services.bracket_service` — imports `convert_datetime` for bracket match kickoff times.
- `scripts/seed_matches.py` (P1-15) — will use `MarkdownParser` to parse group-stage fixtures.
