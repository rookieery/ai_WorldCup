"""Web scraping infrastructure — base scraper, FIFA data scrapers, live scores.

All scrapers inherit from ``BaseScraper`` which provides rate limiting,
exponential-backoff retry, structured logging, and graceful error handling.
"""

from app.scraping.base_scraper import BaseScraper
from app.scraping.data_sync import DataSyncService
from app.scraping.fifa_scraper import FIFAScraper
from app.scraping.live_score_scraper import LiveScoreScraper

__all__ = [
    "BaseScraper",
    "DataSyncService",
    "FIFAScraper",
    "LiveScoreScraper",
]
