# Scripts — Agent Notes

## Architecture
- Scripts run as standalone async Python modules from `football-server/` root.
- Uses `app.config.settings` for DATABASE_URL — no hardcoded connection strings.
- Each seed script creates its own async engine + session (not DI-injected).

## Files

### seed_teams.py
- Entry point: `python -m scripts.seed_teams` or `python scripts/seed_teams.py`
- Imports team data from `scripts/team_data.py` (TEAMS list)
- `seed_teams(session)` — async function that upserts all 48 teams, returns {inserted, updated, skipped}
- `run()` — creates engine, ensures tables exist via `Base.metadata.create_all`, runs seed, disposes engine
- Idempotent: matches by `code` (UNIQUE), updates changed fields or skips unchanged

### team_data.py
- Pure data module: `TEAMS: list[dict[str, Any]]` — 48 team dicts
- Fields: name, name_zh, code, flag (emoji), fifa_ranking, group_label, confederation, world_cup_appearances
- FIFA ranking=0 for 6 playoff qualifiers (CZE, BIH, TUR, SWE, IRQ, COD)

## Patterns for Future Seed Scripts
- Extract data to a separate `_data.py` file to keep scripts under 400-line warning threshold
- Always use `asyncio.run()` for the main entry point
- Support idempotent execution (check existence before insert)
- Log results via standard `logging` module
