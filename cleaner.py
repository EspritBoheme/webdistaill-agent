"""HTML noise removal for token-efficient content extraction."""

from __future__ import annotations

import logging
import re
from typing import Optional

from bs4 import BeautifulSoup, Tag

try:
    from .config.settings import CleanerConfig
except ImportError:
    from config.settings import CleanerConfig

logger = logging.getLogger(__name__)


class Cleaner:
    """Strips noise elements from HTML to produce clean content for AI processing."""

    def __init__(self, config: Optional[CleanerConfig] = None):
        self.config = config or CleanerConfig()

    def clean(self, html: str) -> str:
        """Remove noise elements from raw HTML.

        Strips scripts, styles, navigation, ads, and other non-content elements.

        Args:
            html: Raw HTML string.

        Returns:
            Cleaned HTML with noise removed.
        """
        soup = BeautifulSoup(html, "lxml")

        self._remove_tags(soup)
        self._remove_by_class(soup)
        self._remove_by_id(soup)
        self._remove_empty_tags(soup)
        self._remove_comments(soup)

        cleaned = str(soup)
        cleaned = self._normalize_whitespace(cleaned)

        logger.debug(
            "Cleaned: %d → %d chars (%.1f%% reduction)",
            len(html), len(cleaned),
            (1 - len(cleaned) / max(len(html), 1)) * 100,
        )
        return cleaned

    def _remove_tags(self, soup: BeautifulSoup) -> None:
        for tag_name in self.config.remove_tags:
            for tag in soup.find_all(tag_name):
                tag.decompose()

    def _remove_by_class(self, soup: BeautifulSoup) -> None:
        for cls_pattern in self.config.remove_classes:
            for tag in soup.find_all(class_=re.compile(cls_pattern, re.I)):
                tag.decompose()

    def _remove_by_id(self, soup: BeautifulSoup) -> None:
        for id_pattern in self.config.remove_ids:
            for tag in soup.find_all(id=re.compile(id_pattern, re.I)):
                tag.decompose()

    def _remove_empty_tags(self, soup: BeautifulSoup) -> None:
        for tag in soup.find_all(
            lambda t: isinstance(t, Tag)
            and t.name not in ("br", "hr", "img", "input")
            and not t.get_text(strip=True)
            and not t.find("img")
        ):
            tag.decompose()

    def _remove_comments(self, soup: BeautifulSoup) -> None:
        from bs4 import Comment
        for comment in soup.find_all(string=lambda s: isinstance(s, Comment)):
            comment.extract()

    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        return text.strip()
