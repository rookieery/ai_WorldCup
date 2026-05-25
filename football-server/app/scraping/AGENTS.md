# Scraping Module — Agent Notes

## Architecture
- `BaseScraper` provides rate limiting (`asyncio.Semaphore`), retry (exponential backoff), structured logging, and HTTP client lifecycle.
- `FIFAScraper` extends `BaseScraper` with FIFA-specific parsing logic (`__NEXT_DATA__` JSON extraction).
- All scraped data is validated through `app/schemas/scraper_schema.py` Pydantic models before use.

## Error Handling
- `ScraperError` hierarchy: `ScraperTimeoutError`, `ScraperHTTPError` (with `status_code`), `ScraperParseError`.
- `_is_retryable()` determines which exceptions trigger retry: timeouts, connect errors, HTTP 5xx.
- Non-retryable errors (HTTP 4xx) are raised immediately.
- FIFAScraper gracefully degrades: returns empty schedules/results when page structure doesn't match.

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
async with FIFAScraper() as scraper:
    schedule = await scraper.scrape_match_schedule()
    result = await scraper.scrape_match_result(match_id=42)
```

## Integration Points
- `DataSyncService` (P4-02) will call `FIFAScraper` methods and pass validated data to `LiveService` / `MatchService`.
- Background scheduler (P4-03) will manage the scraping lifecycle via `SCRAPER_ENABLED` flag.
- `RedisKeys.SCRAPER_LOCK` is pre-defined for distributed lock (used in P4-02).