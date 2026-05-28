# Repositories Layer — Agent Notes

## Architecture
- All repos inherit from `BaseRepository[T]` defined in `base.py`.
- Each repo receives an `AsyncSession` at construction; callers manage the session lifecycle.
- No business logic in repos — only SQLAlchemy queries.

## BaseRepository[T] API
- `get_by_id(entity_id)` → raises `NotFoundError` if absent
- `get_by_id_optional(entity_id)` → returns `None` if absent
- `get_all(page, page_size, filters, order_by)` → `(items: Sequence[T], total: int)`
  - `filters`: dict of `{column_name: value}` for equality predicates (None values are skipped)
  - `order_by`: column name string, prefix with `-` for descending
- `create(data: dict)` → entity; wraps `IntegrityError` as `ValidationError`
- `update(entity_id, data: dict)` → entity; partial update (None values skipped)
- `delete(entity_id)` → None; raises `NotFoundError` if absent

## Custom Methods per Repo
- **TeamRepo**: `get_by_code(code)` (unique lookup), `get_by_group(group_label)`
- **MatchRepo**: `get_by_date`, `get_by_stage`, `get_by_status` (paginated); `get_live_matches`, `get_bracket_matches` (non-paginated); `get_by_group_label`, `get_by_team_code`
- **VenueRepo**: base CRUD only
- **GroupRepo**: `get_by_group_label` (sorted by points desc, GD desc, GF desc), `get_group_matches`
- **MatchEventRepo**: `get_by_match(match_id)` (sorted by minute asc)

## Patterns
- Use `result.unique().scalars().all()` for queries with eager-loaded relationships.
- Always use `select()` statements, not legacy `Query` API.
- `_base_query()` can be overridden to add default eager-load options.
