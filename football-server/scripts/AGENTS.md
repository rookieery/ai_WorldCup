# Scripts — Agent Notes

## Architecture
- Scripts run as standalone async Python modules from `football-server/` root.
- Uses `app.config.settings` for DATABASE_URL — no hardcoded connection strings.
- Each seed script creates its own async engine + session (not DI-injected).

## Files

### seed_data.py (P1-16)
- Entry point: `python -m scripts.seed_data`
- **One-click initialization** — orchestrates all seed steps in order:
  1. `seed_venues(session)` — 16 stadiums
  2. `seed_teams(session)` — 48 teams
  3. `seed_matches(session)` — 104 matches (72 group + 32 knockout)
  4. `generate_bracket(session)` — bracket linkage verification
  5. `_init_group_standings(session)` — 48 zero-initialized standings rows
- Fully idempotent — safe to re-run at any time
- Prints a formatted summary table on completion

### generate_bracket.py (P1-16)
- Entry point: `python -m scripts.generate_bracket`
- Defines the complete knockout bracket tree (R32→R16→QF→SF→3rd→F)
- `BRACKET_LINKS` — 30 winner-path links with (src_ext, tgt_ext, position)
- `R32_QUALIFICATION` — maps each R32 match to group positions (from_group, from_position)
- `generate_bracket(session)` — verifies/enforces all next_match_id + position links
- `STAGE_ORDER` and `STAGE_MATCH_COUNT` — canonical stage metadata
- Idempotent: verifies existing links, corrects drift, reports summary
- **Note**: 3rd-place match (3RD_01) has no incoming next_match_id links by design (SF losers go there by convention)

### seed_teams.py
- Entry point: `python -m scripts.seed_teams`
- Imports team data from `scripts/team_data.py` (TEAMS list)
- `seed_teams(session)` — async function that upserts all 48 teams, returns {inserted, updated, skipped}
- Idempotent: matches by `code` (UNIQUE), updates changed fields or skips unchanged

### team_data.py
- Pure data module: `TEAMS: list[dict[str, Any]]` — 48 team dicts
- Fields: name, name_zh, code, flag (emoji), fifa_ranking, group_label, confederation, world_cup_appearances
- FIFA ranking=0 for 6 playoff qualifiers (CZE, BIH, TUR, SWE, IRQ, COD)

### seed_venues.py
- Entry point: `python -m scripts.seed_venues`
- Imports venue data from `scripts/venue_data.py` (VENUES list)
- `seed_venues(session)` — upserts all 16 venues, returns {inserted, updated, skipped}
- Idempotent: matches by `name`

### seed_matches.py
- Entry point: `python -m scripts.seed_matches`
- Seeds all 104 matches: 72 group-stage (from markdown parser) + 32 knockout (from `_KNOCKOUT_DEFS`)
- Creates TBD placeholder team on first run
- Handles bracket linkage internally via `_link_bracket()`
- Idempotent: matches by `external_id`

## Key Data Structures
- `BRACKET_LINKS` (generate_bracket.py) — 30 tuples: (source_ext_id, target_ext_id, position)
- `R32_QUALIFICATION` (generate_bracket.py) — 16 entries: {ext_id: (home_group, home_pos, away_group, away_pos)}
- `_R32_GROUP_MAP` (bracket_service.py) — mirrors R32_QUALIFICATION for API response enrichment

## Patterns for Future Seed Scripts
- Extract data to a separate `_data.py` file to keep scripts under 400-line warning threshold
- Always use `asyncio.run()` for the main entry point
- Support idempotent execution (check existence before insert)
- Log results via standard `logging` module
- Return summary dicts from seed functions for orchestration in seed_data.py
