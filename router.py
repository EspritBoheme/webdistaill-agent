"""Task routing and pipeline orchestration."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

try:
    from .cleaner import Cleaner
    from .config.settings import Settings, get_settings
    from .crawler import Crawler, CrawlResult
    from .formatter import Formatter, FormattedOutput
    from .parser import ContentParser, ParsedContent
    from .summarizer import Summarizer, SummaryResult
except ImportError:
    from cleaner import Cleaner
    from config.settings import Settings, get_settings
    from crawler import Crawler, CrawlResult
    from formatter import Formatter, FormattedOutput
    from parser import ContentParser, ParsedContent
    from summarizer import Summarizer, SummaryResult

logger = logging.getLogger(__name__)


class TaskMode(str, Enum):
    DEFAULT = "default"
    TECHNICAL = "technical"
    RAW = "raw"           # No AI summarization
    FULL = "full"         # All metadata + summary + links


@dataclass
class Task:
    """Represents a single distillation task."""
    url: str
    mode: TaskMode = TaskMode.DEFAULT
    output_format: str = "markdown"
    options: dict[str, Any] = field(default_factory=dict)

    # Stage results
    crawl_result: Optional[CrawlResult] = None
    cleaned_html: Optional[str] = None
    parsed_content: Optional[ParsedContent] = None
    summary_result: Optional[SummaryResult] = None
    formatted_output: Optional[FormattedOutput] = None
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None


# Type alias for pipeline stages
Stage = Callable[[Task], Task]


class Pipeline:
    """Composable processing pipeline."""

    def __init__(self):
        self._stages: list[Stage] = []

    def pipe(self, stage: Stage) -> "Pipeline":
        self._stages.append(stage)
        return self

    def run(self, task: Task) -> Task:
        for stage in self._stages:
            if task.error:
                break
            try:
                task = stage(task)
            except Exception as exc:
                task.error = f"Pipeline error in {stage.__name__}: {exc}"
                logger.error(task.error)
        return task


class Router:
    """Orchestrates the distillation pipeline based on task configuration."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()

    def create_task(
        self,
        url: str,
        mode: str = "default",
        output_format: str = "markdown",
        **options,
    ) -> Task:
        return Task(
            url=url,
            mode=TaskMode(mode),
            output_format=output_format,
            options=options,
        )

    def execute(self, task: Task) -> Task:
        """Run the full pipeline for a task."""
        logger.info("Executing task: url=%s, mode=%s", task.url, task.mode)

        pipeline = self._build_pipeline(task)
        task = pipeline.run(task)

        if task.ok:
            logger.info("Task completed: %s", task.url)
        else:
            logger.error("Task failed: %s — %s", task.url, task.error)

        return task

    def _build_pipeline(self, task: Task) -> Pipeline:
        pipeline = Pipeline()

        # Stage 1: Crawl
        pipeline.pipe(self._stage_crawl)

        # Stage 2: Clean
        pipeline.pipe(self._stage_clean)

        # Stage 3: Parse
        pipeline.pipe(self._stage_parse)

        # Stage 4: Summarize (skip for RAW mode)
        if task.mode != TaskMode.RAW:
            pipeline.pipe(self._stage_summarize)

        # Stage 5: Format
        pipeline.pipe(self._stage_format)

        return pipeline

    def _stage_crawl(self, task: Task) -> Task:
        with Crawler(self.settings.crawler) as crawler:
            task.crawl_result = crawler.fetch(task.url)
            if not task.crawl_result.ok:
                task.error = f"Crawl failed: {task.crawl_result.error}"
        return task

    def _stage_clean(self, task: Task) -> Task:
        cleaner = Cleaner(self.settings.cleaner)
        task.cleaned_html = cleaner.clean(task.crawl_result.html)
        return task

    def _stage_parse(self, task: Task) -> Task:
        parser = ContentParser()
        task.parsed_content = parser.parse(
            task.cleaned_html,
            source_url=task.crawl_result.url,
        )
        return task

    def _stage_summarize(self, task: Task) -> Task:
        summarizer = Summarizer(self.settings.summarizer)
        task.summary_result = summarizer.summarize(
            content=task.parsed_content.content,
            title=task.parsed_content.title,
            url=task.crawl_result.url,
            mode="technical" if task.mode in (TaskMode.TECHNICAL, TaskMode.FULL) else "default",
        )
        return task

    def _stage_format(self, task: Task) -> Task:
        formatter = Formatter(output_format=task.output_format)
        task.formatted_output = formatter.format(
            parsed=task.parsed_content,
            summary=task.summary_result,
        )
        return task
