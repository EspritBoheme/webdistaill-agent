"""Output formatting for Markdown and JSON."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Optional

try:
    from .parser import ParsedContent
    from .summarizer import SummaryResult
except ImportError:
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

        if summary:
            parts.append("## Distillation\n")
            if summary.summary:
                parts.append(f"{summary.summary}\n")

            self._append_list(parts, "Key Points", summary.key_points)
            self._append_list(parts, "Key Concepts", summary.key_concepts)
            self._append_list(parts, "Steps", summary.steps)
            self._append_list(parts, "Warnings", summary.warnings)

            compact = []
            if summary.topics:
                compact.append(f"**Topics**: {', '.join(summary.topics)}")
            if summary.technical_terms:
                compact.append(f"**Terms**: {', '.join(summary.technical_terms)}")
            if summary.code_languages:
                compact.append(f"**Languages**: {', '.join(summary.code_languages)}")
            if summary.api_references:
                compact.append(f"**API References**: {', '.join(summary.api_references)}")
            if summary.dependencies:
                compact.append(f"**Dependencies**: {', '.join(summary.dependencies)}")
            if compact:
                parts.append("\n".join(compact) + "\n")

            meta = [value for value in [summary.content_type, summary.difficulty] if value]
            if summary.reading_time_minutes:
                meta.append(f"~{summary.reading_time_minutes} min")
            if meta:
                parts.append(f"**Profile**: {' | '.join(meta)}\n")

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
            "distillation": self._summary_to_dict(summary) if summary else None,
            "headings": parsed.headings,
            "links": parsed.links,
            "content": parsed.content,
        }

        if data["distillation"] is None:
            del data["distillation"]

        return json.dumps(data, ensure_ascii=False, indent=2)

    @staticmethod
    def _append_list(parts: list[str], title: str, items: list[str]) -> None:
        if not items:
            return
        parts.append(f"### {title}\n")
        for item in items:
            parts.append(f"- {item}")
        parts.append("")

    @staticmethod
    def _summary_to_dict(summary: SummaryResult) -> dict:
        return {
            "summary": summary.summary,
            "key_points": summary.key_points,
            "topics": summary.topics,
            "technical_terms": summary.technical_terms,
            "content_type": summary.content_type,
            "difficulty": summary.difficulty,
            "reading_time_minutes": summary.reading_time_minutes,
            "key_concepts": summary.key_concepts,
            "code_languages": summary.code_languages,
            "api_references": summary.api_references,
            "dependencies": summary.dependencies,
            "steps": summary.steps,
            "warnings": summary.warnings,
        }
