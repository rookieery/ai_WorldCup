"""Web scraping infrastructure — base scraper, FIFA data scrapers, live scores, scheduler.

All scrapers inherit from ``BaseScraper`` which provides rate limiting,
exponential-backoff retry, structured logging, and graceful error handling.
The :class:`ScraperScheduler` orchestrates periodic scraping tasks.
"""

from app.scraping.base_scraper import BaseScraper
from app.scraping.data_sync import DataSyncService
from app.scraping.fifa_scraper import FIFAScraper
from app.scraping.live_score_scraper import LiveScoreScraper
from app.scraping.scheduler import ScraperScheduler

__all__ = [
    "BaseScraper",
    "DataSyncService",
    "FIFAScraper",
    "LiveScoreScraper",
    "ScraperScheduler",
]
