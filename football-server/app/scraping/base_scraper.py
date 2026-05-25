"""Base scraper - rate limiting, retry with exponential backoff, structured logging.

Every concrete scraper inherits from ``BaseScraper`` and calls
:meth:`fetch` to make HTTP requests.  The base class takes care of:

* **Concurrency control** - an ``asyncio.Semaphore`` limits in-flight
  requests to ``SCRAPER_CONCURRENCY`` (default 3).
* **Retry with exponential backoff** - transient failures (timeouts,
  HTTP 5xx, network errors) are retried up to ``SCRAPER_RETRY_MAX``
  times (default 3) with ``2 ** attempt`` second delays.
* **Structured logging** - each request logs URL, status code, elapsed
  time, and retry attempts.
* **Error categorisation** - distinguishes timeout, HTTP status, and
  parse failures so callers can decide what to do.

Design notes
------------
The class creates one ``httpx.AsyncClient`` per instance that is reused
for the entire scraping session.  Callers should invoke :meth:`close`
when finished (or use the async context-manager protocol).
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


# ── Exception hierarchy ─────────────────────────────────────────────────


class ScraperError(Exception):
    """Base exception for all scraping failures."""

    def __init__(self, url: str, message: str = "Scraping failed") -> None:
        self.url = url
        super().__init__(f"[{url}] {message}")


class ScraperTimeoutError(ScraperError):
    """Raised when an HTTP request times out."""

    def __init__(self, url: str) -> None:
        super().__init__(url, "Request timed out")


class ScraperHTTPError(ScraperError):
    """Raised when the server responds with an error status code."""

    def __init__(self, url: str, status_code: int) -> None:
        self.status_code = status_code
        super().__init__(url, f"HTTP {status_code}")


class ScraperParseError(ScraperError):
    """Raised when the response body cannot be parsed into the expected shape."""

    def __init__(self, url: str, detail: str = "") -> None:
        super().__init__(url, f"Parse error: {detail}")


# ── Retryable check ────────────────────────────────────────────────────


def _is_retryable(exc: Exception) -> bool:
    """Return ``True`` if the exception is transient and worth retrying."""
    if isinstance(exc, (httpx.TimeoutException, httpx.ConnectError)):
        return True
    if isinstance(exc, ScraperHTTPError) and exc.status_code >= 500:
        return True
    return False


# ── BaseScraper ────────────────────────────────────────────────────────


class BaseScraper:
    """Abstract base for all scrapers.

    Parameters
    ----------
    concurrency:
        Maximum number of concurrent HTTP requests.
    timeout:
        Per-request timeout in seconds.
    max_retries:
        Maximum number of retry attempts for transient failures.
    headers:
        Optional default headers to send with every request.
    """

    def __init__(
        self,
        *,
        concurrency: int = settings.SCRAPER_CONCURRENCY,
        timeout: int = settings.SCRAPER_TIMEOUT,
        max_retries: int = settings.SCRAPER_RETRY_MAX,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        self._semaphore = asyncio.Semaphore(concurrency)
        self._timeout = timeout
        self._max_retries = max_retries
        self._default_headers: dict[str, str] = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        if headers:
            self._default_headers.update(headers)
        self._client: Optional[httpx.AsyncClient] = None

    # ── Context manager ────────────────────────────────────────────────

    async def __aenter__(self) -> "BaseScraper":
        await self._ensure_client()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    # ── Client lifecycle ───────────────────────────────────────────────

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Lazily create the shared ``httpx.AsyncClient``."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self._timeout, connect=10.0),
                headers=self._default_headers,
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        """Gracefully close the HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
            logger.debug("Scraper HTTP client closed")

    # ── Core fetch with rate limit + retry ─────────────────────────────

    async def fetch(
        self,
        url: str,
        *,
        params: Optional[dict[str, Any]] = None,
    ) -> str:
        """Fetch a URL with rate limiting and automatic retry.

        Returns the response body as text.  Raises a subclass of
        :class:`ScraperError` when all retries are exhausted.
        """
        client = await self._ensure_client()
        last_exc: Optional[Exception] = None

        async with self._semaphore:
            for attempt in range(1, self._max_retries + 1):
                start = time.monotonic()
                try:
                    response = await client.get(url, params=params)
                    elapsed = time.monotonic() - start
                    logger.info(
                        "GET %s -> %d (%.2fs, attempt %d/%d)",
                        url,
                        response.status_code,
                        elapsed,
                        attempt,
                        self._max_retries,
                    )

                    if response.status_code >= 500:
                        raise ScraperHTTPError(url, response.status_code)
                    if response.status_code >= 400:
                        raise ScraperHTTPError(url, response.status_code)

                    return response.text

                except httpx.TimeoutException:
                    elapsed = time.monotonic() - start
                    last_exc = ScraperTimeoutError(url)
                    logger.warning(
                        "GET %s -> timeout (%.2fs, attempt %d/%d)",
                        url,
                        elapsed,
                        attempt,
                        self._max_retries,
                    )

                except httpx.HTTPStatusError as exc:
                    elapsed = time.monotonic() - start
                    last_exc = ScraperHTTPError(url, exc.response.status_code)
                    logger.warning(
                        "GET %s -> HTTP %d (%.2fs, attempt %d/%d)",
                        url,
                        exc.response.status_code,
                        elapsed,
                        attempt,
                        self._max_retries,
                    )

                except httpx.ConnectError:
                    elapsed = time.monotonic() - start
                    last_exc = ScraperHTTPError(url, 0)
                    logger.warning(
                        "GET %s -> connection error (%.2fs, attempt %d/%d)",
                        url,
                        elapsed,
                        attempt,
                        self._max_retries,
                    )

                except ScraperHTTPError as exc:
                    last_exc = exc
                    logger.warning(
                        "GET %s -> %s (attempt %d/%d)",
                        url,
                        exc,
                        attempt,
                        self._max_retries,
                    )

                # Decide whether to retry
                if last_exc is not None and _is_retryable(last_exc):
                    if attempt < self._max_retries:
                        backoff = 2 ** attempt
                        logger.info("Retrying in %ds ...", backoff)
                        await asyncio.sleep(backoff)
                    continue
                else:
                    # Non-retryable error -- raise immediately
                    raise last_exc from None

        # All retries exhausted
        if last_exc is not None:
            raise last_exc from None
        raise ScraperError(url, "All retries exhausted with no recorded error")