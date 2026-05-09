"""AI-powered content summarization via OpenAI API."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from openai import OpenAI

from config.settings import SummarizerConfig

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a precise content distillation engine. Your task is to extract \
structured knowledge from web content.

Rules:
- Output valid JSON only, no markdown fences.
- Be factual, do not invent information.
- Preserve key technical details, names, and numbers.
- If content is insufficient for a field, use null.
"""

SUMMARY_PROMPT_TEMPLATE = """\
Analyze the following web content and produce a structured summary.

Title: {title}
URL: {url}

Content:
{content}

Return a JSON object with these fields:
{{
  "summary": "2-3 sentence concise summary",
  "key_points": ["point1", "point2", ...],
  "topics": ["topic1", "topic2", ...],
  "technical_terms": ["term1", "term2", ...],
  "content_type": "article | documentation | tutorial | news | reference | other",
  "reading_time_minutes": <int>,
  "difficulty": "beginner | intermediate | advanced"
}}
"""

TECHNICAL_PROMPT_TEMPLATE = """\
Extract technical documentation structure from this content.

Title: {title}
URL: {url}

Content:
{content}

Return a JSON object:
{{
  "summary": "technical summary",
  "key_concepts": ["concept1", ...],
  "code_languages": ["language1", ...],
  "api_references": ["ref1", ...],
  "dependencies": ["dep1", ...],
  "steps": ["step1", ...],
  "warnings": ["warning1", ...]
}}
"""


@dataclass
class SummaryResult:
    """Structured AI summary."""
    summary: str = ""
    key_points: list[str] = None
    topics: list[str] = None
    technical_terms: list[str] = None
    content_type: str = ""
    reading_time_minutes: int = 0
    difficulty: str = ""
    raw_response: str = ""

    def __post_init__(self):
        if self.key_points is None:
            self.key_points = []
        if self.topics is None:
            self.topics = []
        if self.technical_terms is None:
            self.technical_terms = []


class Summarizer:
    """Generates structured summaries using OpenAI models."""

    def __init__(self, config: Optional[SummarizerConfig] = None):
        self.config = config or SummarizerConfig()
        self._client = OpenAI(api_key=self.config.api_key)

    def summarize(
        self,
        content: str,
        title: str = "",
        url: str = "",
        mode: str = "default",
    ) -> SummaryResult:
        """Summarize content with AI.

        Args:
            content: Cleaned text content.
            title: Page title for context.
            url: Source URL for context.
            mode: "default" or "technical".

        Returns:
            SummaryResult with structured summary data.
        """
        truncated = self._truncate(content)
        prompt_template = (
            TECHNICAL_PROMPT_TEMPLATE if mode == "technical"
            else SUMMARY_PROMPT_TEMPLATE
        )
        user_prompt = prompt_template.format(
            title=title or "Untitled",
            url=url or "Unknown",
            content=truncated,
        )

        logger.info("Summarizing: title=%r, chars=%d", title, len(truncated))

        try:
            response = self._client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                response_format={"type": "json_object"},
            )

            raw = response.choices[0].message.content or ""
            return self._parse_response(raw)

        except Exception as exc:
            logger.error("Summarization failed: %s", exc)
            return SummaryResult(
                summary=f"Summarization failed: {exc}",
                raw_response="",
            )

    def _truncate(self, text: str) -> str:
        if len(text) <= self.config.max_input_chars:
            return text
        logger.warning(
            "Truncating input: %d → %d chars",
            len(text), self.config.max_input_chars,
        )
        return text[: self.config.max_input_chars]

    @staticmethod
    def _parse_response(raw: str) -> SummaryResult:
        import json

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Failed to parse AI response as JSON")
            return SummaryResult(raw_response=raw)

        return SummaryResult(
            summary=data.get("summary", ""),
            key_points=data.get("key_points", []),
            topics=data.get("topics", []),
            technical_terms=data.get("technical_terms", []),
            content_type=data.get("content_type", ""),
            reading_time_minutes=data.get("reading_time_minutes", 0),
            difficulty=data.get("difficulty", ""),
            raw_response=raw,
        )
