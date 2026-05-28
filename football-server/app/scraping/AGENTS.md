# Scraping Module — Agent Notes

## Architecture
- `BaseScraper` provides rate limiting (`asyncio.Semaphore`), retry (exponential backoff), structured logging, and HTTP client lifecycle.
- `FIFAScraper` extends `BaseScraper` with FIFA-specific parsing logic (`__NEXT_DATA__` JSON extraction).
- `LiveScoreScraper` extends `BaseScraper` for real-time live score scraping from the FIFA schedule page.
- `DataSyncService` orchestrates syncing scraped data into Redis (live) and SQLite (results, standings).
- All scraped data is validated through `app/schemas/scraper_schema.py` Pydantic models before use.

## Error Handling
- `ScraperError` hierarchy: `ScraperTimeoutError`, `ScraperHTTPError` (with `status_code`), `ScraperParseError`.
- `_is_retryable()` determines which exceptions trigger retry: timeouts, connect errors, HTTP 5xx.
- Non-retryable errors (HTTP 4xx) are raised immediately.
- FIFAScraper and LiveScoreScraper gracefully degrade: return empty batches when page structure doesn't match.

## LiveScoreScraper
- `scrape_live_scores() -> ScrapedLiveScoreBatch` — fetches the schedule page, filters for live matches, returns validated live score data.
- Activity level estimation: heuristic based on event types/weights and match minute progress.
- Accepts same match status variants: "live", "in_play", "halftime", "1h", "2h", "et", "ht".
- Reuses `_extract_next_data()` from `fifa_scraper.py`.

## DataSyncService
- `sync_live_scores(batch)` → int — syncs live score batch to Redis via `LiveService`.
- `sync_match_result(result)` → Optional[Match] — syncs finished match result to SQLite (updates scores, status, events).
- `sync_group_standings()` → int — recalculates all 12 group standings from finished matches.
- Distributed lock: `_acquire_lock()` / `_release_lock()` using Redis `SET NX EX` with Lua-script safe release. Falls back to `asyncio.Lock` when Redis unavailable.
- Lock key: `RedisKeys.SCRAPER_LOCK` (=`scraper:lock`), TTL: 60s.
- External ID resolution: `_resolve_match_id()` queries DB for `external_id`, falls back to integer parsing.

## LiveService Extensions (P4-02)
- `apply_sync_data(match_id, *, home_score, away_score, status, activity_level, events)` — batched update for DataSyncService. Performs one Redis write+read cycle instead of multiple individual calls.
- Redis implementation: `_apply_sync_data_redis()` — single pipeline HSET+HGETALL.
- Memory fallback: `_apply_sync_data_memory()` — single dict update.

## Configuration
All scraper settings are in `app/config.py` and can be overridden via env vars:
- `SCRAPER_ENABLED` — master switch (default: false)
- `FIFA_SCHEDULE_URL` — schedule page URL
- `FIFA_MATCH_URL` — match page base URL
- `SCRAPER_CONCURRENCY` — max concurrent requests (default: 3)
- `SCRAPER_TIMEOUT` — per-request timeout in seconds (default: 30)
- `SCRAPER_RETRY_MAX` — max retry attempts (default: 3)

## Usage Pattern
```python
# Scraping live scores
async with LiveScoreScraper() as scraper:
    batch = await scraper.scrape_live_scores()

# Syncing to storage
sync = DataSyncService(redis=redis, session=session)
synced = await sync.sync_live_scores(batch)

# With distributed lock
token = await sync._acquire_lock()
try:
    await sync.sync_match_result(result)
    await sync.sync_group_standings()
finally:
    await sync._release_lock(token)
```

## Integration Points
- Background scheduler (P4-03) will manage the scraping lifecycle via `SCRAPER_ENABLED` flag.
- `DataSyncService` calls `LiveService.apply_sync_data()` and individual update methods.
- `DataSyncService` uses `MatchRepository`, `MatchEventRepository`, `GroupRepository` for DB operations.