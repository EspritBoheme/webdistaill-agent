"""Content and metadata extraction from cleaned HTML."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)


@dataclass
class ParsedContent:
    """Structured output from the parser stage."""
    title: str = ""
    content: str = ""
    description: str = ""
    author: str = ""
    publish_date: str = ""
    canonical_url: str = ""
    language: str = ""
    og_title: str = ""
    og_image: str = ""
    og_description: str = ""
    headings: list[dict[str, str]] = field(default_factory=list)
    links: list[dict[str, str]] = field(default_factory=list)
    word_count: int = 0

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "description": self.description,
            "author": self.author,
            "publish_date": self.publish_date,
            "canonical_url": self.canonical_url,
            "language": self.language,
            "word_count": self.word_count,
            "headings": self.headings,
        }


class ContentParser:
    """Extracts structured content and metadata from cleaned HTML."""

    def parse(self, html: str, source_url: str = "") -> ParsedContent:
        """Parse cleaned HTML into structured content.

        Args:
            html: Cleaned HTML string.
            source_url: Original URL for resolving relative links.

        Returns:
            ParsedContent with extracted metadata and text.
        """
        soup = BeautifulSoup(html, "lxml")
        result = ParsedContent()

        result.title = self._extract_title(soup)
        result.description = self._extract_meta(soup, "description")
        result.author = self._extract_meta(soup, "author")
        result.canonical_url = self._extract_canonical(soup, source_url)
        result.language = self._extract_language(soup)

        # Open Graph
        result.og_title = self._extract_og(soup, "og:title")
        result.og_image = self._extract_og(soup, "og:image")
        result.og_description = self._extract_og(soup, "og:description")

        # Headings
        result.headings = self._extract_headings(soup)

        # Main content
        result.content = self._extract_main_content(soup)
        result.word_count = len(result.content.split())

        # Links
        result.links = self._extract_links(soup, source_url)

        logger.info(
            "Parsed: title=%r, words=%d, headings=%d",
            result.title, result.word_count, len(result.headings),
        )
        return result

    def _extract_title(self, soup: BeautifulSoup) -> str:
        if soup.title and soup.title.string:
            return soup.title.string.strip()
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        return ""

    def _extract_meta(self, soup: BeautifulSoup, name: str) -> str:
        tag = soup.find("meta", attrs={"name": name})
        return tag.get("content", "").strip() if tag else ""

    def _extract_canonical(self, soup: BeautifulSoup, source_url: str) -> str:
        tag = soup.find("link", rel="canonical")
        if tag and tag.get("href"):
            return tag["href"]
        return source_url

    def _extract_language(self, soup: BeautifulSoup) -> str:
        html_tag = soup.find("html")
        if html_tag:
            return html_tag.get("lang", "")
        return ""

    def _extract_og(self, soup: BeautifulSoup, property_name: str) -> str:
        tag = soup.find("meta", attrs={"property": property_name})
        return tag.get("content", "").strip() if tag else ""

    def _extract_headings(self, soup: BeautifulSoup) -> list[dict[str, str]]:
        headings = []
        for tag in soup.find_all(re.compile(r"^h[1-6]$")):
            headings.append({
                "level": tag.name,
                "text": tag.get_text(strip=True),
            })
        return headings

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        candidates = soup.select("article, main, [role='main'], .post-content, .entry-content")
        if not candidates:
            candidates = soup.find_all(["section", "div", "body"])

        best = max(
            candidates,
            key=lambda tag: len(tag.get_text(separator=" ", strip=True)),
            default=soup,
        )
        return self._normalize_text(best.get_text(separator="\n", strip=True))

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> list[dict[str, str]]:
        links = []
        seen = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith(("#", "javascript:", "mailto:")):
                continue
            resolved = urljoin(base_url, href) if base_url else href
            if resolved not in seen:
                seen.add(resolved)
                links.append({
                    "text": a.get_text(strip=True)[:200],
                    "url": resolved,
                })
        return links[:100]

    @staticmethod
    def _normalize_text(text: str) -> str:
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        return text.strip()
