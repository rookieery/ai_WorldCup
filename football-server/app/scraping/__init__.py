"""Web scraping infrastructure — base scraper, FIFA data scrapers.

All scrapers inherit from ``BaseScraper`` which provides rate limiting,
exponential-backoff retry, structured logging, and graceful error handling.
"""

from app.scraping.base_scraper import BaseScraper
from app.scraping.fifa_scraper import FIFAScraper

__all__ = [
    "BaseScraper",
    "FIFAScraper",
]
