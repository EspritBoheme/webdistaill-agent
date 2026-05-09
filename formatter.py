"""Output formatting for Markdown and JSON."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Optional

from parser import ParsedContent
from summarizer import SummaryResult

logger = logging.getLogger(__name__)


@dataclass
class FormattedOutput:
    """Final formatted result."""
    content: str
    format: str
    size: int = 0

    def __post_init__(self):
        self.size = len(self.content)


class Formatter:
    """Renders parsed content and AI summaries into final output formats."""

    def __init__(self, output_format: str = "markdown"):
        self.output_format = output_format

    def format(
        self,
        parsed: ParsedContent,
        summary: Optional[SummaryResult] = None,
    ) -> FormattedOutput:
        """Format parsed content and optional summary.

        Args:
            parsed: ParsedContent from the parser stage.
            summary: Optional SummaryResult from the summarizer stage.

        Returns:
            FormattedOutput with rendered content string.
        """
        if self.output_format == "json":
            content = self._to_json(parsed, summary)
        else:
            content = self._to_markdown(parsed, summary)

        logger.info(
            "Formatted: %s, %d chars",
            self.output_format, len(content),
        )
        return FormattedOutput(content=content, format=self.output_format)

    def _to_markdown(
        self,
        parsed: ParsedContent,
        summary: Optional[SummaryResult],
    ) -> str:
        parts: list[str] = []

        # Header
        parts.append(f"# {parsed.title or 'Untitled'}\n")

        # Metadata
        meta_lines: list[str] = []
        if parsed.canonical_url:
            meta_lines.append(f"**URL**: {parsed.canonical_url}")
        if parsed.author:
            meta_lines.append(f"**Author**: {parsed.author}")
        if parsed.publish_date:
            meta_lines.append(f"**Date**: {parsed.publish_date}")
        if parsed.language:
            meta_lines.append(f"**Language**: {parsed.language}")
        if parsed.word_count:
            meta_lines.append(f"**Words**: {parsed.word_count}")
        if meta_lines:
            parts.append("\n".join(meta_lines) + "\n")

        # AI Summary
        if summary:
            parts.append("## AI Summary\n")
            parts.append(f"{summary.summary}\n")

            if summary.key_points:
                parts.append("### Key Points\n")
                for point in summary.key_points:
                    parts.append(f"- {point}")
                parts.append("")

            if summary.topics:
                parts.append(f"**Topics**: {', '.join(summary.topics)}\n")

            if summary.technical_terms:
                parts.append(f"**Terms**: {', '.join(summary.technical_terms)}\n")

            if summary.content_type:
                parts.append(f"**Type**: {summary.content_type} | ")
                parts.append(f"**Difficulty**: {summary.difficulty} | ")
                parts.append(f"**Reading time**: ~{summary.reading_time_minutes} min\n")

        # Headings outline
        if parsed.headings:
            parts.append("## Document Structure\n")
            for h in parsed.headings:
                level = int(h["level"][1])
                indent = "  " * (level - 1)
                parts.append(f"{indent}- {h['text']}")
            parts.append("")

        # Main content
        parts.append("## Content\n")
        parts.append(parsed.content)

        return "\n".join(parts)

    def _to_json(
        self,
        parsed: ParsedContent,
        summary: Optional[SummaryResult],
    ) -> str:
        data = {
            "metadata": parsed.to_dict(),
            "content": parsed.content,
        }

        if summary:
            data["ai_summary"] = {
                "summary": summary.summary,
                "key_points": summary.key_points,
                "topics": summary.topics,
                "technical_terms": summary.technical_terms,
                "content_type": summary.content_type,
                "difficulty": summary.difficulty,
                "reading_time_minutes": summary.reading_time_minutes,
            }

        data["headings"] = parsed.headings

        return json.dumps(data, ensure_ascii=False, indent=2)
