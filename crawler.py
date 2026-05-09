"""HTTP crawler with retry logic and user-agent rotation."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.settings import CrawlerConfig

logger = logging.getLogger(__name__)


class CrawlError(Exception):
    """Raised when crawling fails after all retries."""


@dataclass
class CrawlResult:
    """Raw crawl output."""
    url: str
    html: str
    status_code: int
    encoding: str = "utf-8"
    elapsed: float = 0.0
    content_type: str = ""
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None and 200 <= self.status_code < 300


class Crawler:
    """Fetches raw HTML from public URLs with retry and timeout handling."""

    def __init__(self, config: Optional[CrawlerConfig] = None):
        self.config = config or CrawlerConfig()
        self._session = self._build_session()

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.retry_backoff,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        session.headers.update({"User-Agent": self.config.user_agent})
        return session

    def fetch(self, url: str) -> CrawlResult:
        """Fetch a single URL and return raw HTML.

        Args:
            url: Fully qualified public URL.

        Returns:
            CrawlResult with HTML content and metadata.

        Raises:
            CrawlError: On network or HTTP errors after retries are exhausted.
        """
        start = time.monotonic()
        logger.info("Crawling: %s", url)

        try:
            resp = self._session.get(
                url,
                timeout=self.config.timeout,
                allow_redirects=True,
            )
            resp.raise_for_status()

            content_length = len(resp.content)
            if content_length > self.config.max_content_length:
                raise CrawlError(
                    f"Response too large: {content_length} bytes "
                    f"(max {self.config.max_content_length})"
                )

            elapsed = time.monotonic() - start
            logger.info(
                "Crawled OK: %s [%d] %.2fs",
                url, resp.status_code, elapsed,
            )

            return CrawlResult(
                url=resp.url,
                html=resp.text,
                status_code=resp.status_code,
                encoding=resp.encoding or "utf-8",
                elapsed=elapsed,
                content_type=resp.headers.get("Content-Type", ""),
            )

        except requests.HTTPError as exc:
            elapsed = time.monotonic() - start
            code = exc.response.status_code if exc.response else 0
            logger.error("Crawl HTTP error: %s — %s", url, exc)
            return CrawlResult(
                url=url,
                html=exc.response.text if exc.response else "",
                status_code=code,
                elapsed=elapsed,
                error=str(exc),
            )
        except requests.RequestException as exc:
            elapsed = time.monotonic() - start
            logger.error("Crawl failed: %s — %s", url, exc)
            return CrawlResult(
                url=url,
                html="",
                status_code=0,
                elapsed=elapsed,
                error=str(exc),
            )

    def close(self) -> None:
        self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
