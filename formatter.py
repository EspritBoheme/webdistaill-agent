"""Output formatting for Markdown, JSON, and HTML visualization modes."""

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

    def __init__(self, output_format: str = "markdown", mode: str = "default"):
        self.output_format = output_format
        self.mode = mode

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
        elif self.output_format == "html":
            content = self._to_html(parsed, summary)
        else:
            content = self._to_markdown(parsed, summary)

        logger.info(
            "Formatted: %s, %d chars",
            self.output_format, len(content),
        )
        return FormattedOutput(content=content, format=self.output_format)

    # ------------------------------------------------------------------
    # Markdown
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # JSON
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # HTML dispatch
    # ------------------------------------------------------------------

    def _to_html(
        self,
        parsed: ParsedContent,
        summary: Optional[SummaryResult],
    ) -> str:
        if self.mode == "mindmap":
            return self._to_mindmap_html(parsed, summary)
        elif self.mode == "timeline":
            return self._to_timeline_html(parsed, summary)
        elif self.mode == "glossary":
            return self._to_glossary_html(parsed, summary)
        else:
            return self._to_markdown(parsed, summary)

    # ------------------------------------------------------------------
    # Mindmap HTML (Markmap)
    # ------------------------------------------------------------------

    def _to_mindmap_html(
        self,
        parsed: ParsedContent,
        summary: Optional[SummaryResult],
    ) -> str:
        page_title = parsed.title or "Mindmap"
        markdown = self._mindmap_tree_to_markdown(summary)

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{self._escape_html(page_title)} — Mindmap</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f8fafc; }}
  #mindmap {{ width: 100vw; height: 100vh; }}
  .toolbar {{
    position: fixed; bottom: 1.25rem; right: 1.25rem;
    display: flex; gap: 0.5rem; z-index: 100;
  }}
  .toolbar button {{
    padding: 0.5rem 1rem; border: none; border-radius: 6px;
    background: #4f46e5; color: #fff; cursor: pointer;
    font-size: 0.875rem; font-weight: 500;
    box-shadow: 0 2px 8px rgba(79,70,229,0.3);
    transition: background 0.15s;
  }}
  .toolbar button:hover {{ background: #4338ca; }}
  .source-link {{
    position: fixed; bottom: 1.25rem; left: 1.25rem; z-index: 100;
    font-size: 0.75rem; color: #94a3b8;
  }}
  .source-link a {{ color: #6366f1; text-decoration: none; }}
</style>
</head>
<body>
<div id="mindmap"></div>
<div class="toolbar">
  <button onclick="mm.fit()">适应</button>
  <button onclick="mm.rescale(1.5)">放大</button>
  <button onclick="mm.rescale(0.67)">缩小</button>
</div>
<div class="source-link">
  {self._escape_html(parsed.canonical_url or '')}
</div>
<script src="https://cdn.jsdelivr.net/npm/markmap-autoloader@0.17"></script>
<script>
window.addEventListener('load', () => {{
  setTimeout(() => {{
    const svg = document.querySelector('#mindmap svg');
    if (svg && window.mm) {{ /* mm set by autoloader */ }}
  }}, 100);
}});
</script>
<script type="text/markdown">{markdown}</script>
</body>
</html>"""

    def _mindmap_tree_to_markdown(self, summary: Optional[SummaryResult]) -> str:
        """Convert AI mindmap JSON tree to markdown for Markmap rendering."""
        if not summary or not summary.data:
            return "# (No data)"

        mindmap_data = summary.data.get("mindmap")
        if not mindmap_data:
            return "# (Empty mindmap)"

        lines: list[str] = []
        root_label = mindmap_data.get("label", summary.data.get("title", "Untitled"))
        lines.append(f"# {self._escape_md(root_label)}")

        def _walk(children: list, depth: int) -> None:
            if depth > 4 or not children:
                return
            prefix = "#" * (depth + 1)
            for child in children:
                if isinstance(child, dict):
                    label = child.get("label", "")
                    lines.append(f"{prefix} {self._escape_md(label)}")
                    _walk(child.get("children", []), depth + 1)
                elif isinstance(child, str):
                    lines.append(f"- {self._escape_md(child)}")

        _walk(mindmap_data.get("children", []), 1)
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Timeline HTML (Pure CSS)
    # ------------------------------------------------------------------

    def _to_timeline_html(
        self,
        parsed: ParsedContent,
        summary: Optional[SummaryResult],
    ) -> str:
        page_title = parsed.title or "Timeline"
        events = self._get_data_field(summary, "events", [])

        event_cards = ""
        for i, ev in enumerate(events):
            date = self._escape_html(ev.get("date", ""))
            title = self._escape_html(ev.get("title", ""))
            desc = self._escape_html(ev.get("description", ""))
            importance = ev.get("importance", "minor")
            side = "left" if i % 2 == 0 else "right"
            badge = '<span class="badge major">重要</span>' if importance == "major" else ""

            event_cards += f"""
    <div class="event {side}">
      <div class="card">
        <div class="card-date">{date}</div>
        <h3>{title}{badge}</h3>
        <p>{desc}</p>
      </div>
    </div>"""

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{self._escape_html(page_title)} — Timeline</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: #f8fafc; color: #1e293b;
    padding: 2rem;
  }}
  h1 {{ text-align: center; margin-bottom: 2.5rem; font-size: 1.75rem; color: #0f172a; }}
  .timeline {{
    position: relative; max-width: 860px; margin: 0 auto; padding: 1rem 0;
  }}
  .timeline::before {{
    content: ''; position: absolute; left: 50%; top: 0; bottom: 0;
    width: 3px; background: linear-gradient(180deg, #6366f1, #a78bfa);
    transform: translateX(-50%);
  }}
  .event {{
    position: relative; width: 50%; padding: 0.75rem 2rem; margin-bottom: 0.5rem;
  }}
  .event.left {{ left: 0; text-align: right; padding-right: 2.75rem; }}
  .event.right {{ left: 50%; text-align: left; padding-left: 2.75rem; }}
  .event::before {{
    content: ''; position: absolute; top: 1.25rem;
    width: 12px; height: 12px; border-radius: 50%;
    background: #6366f1; border: 3px solid #c7d2fe;
    z-index: 1;
  }}
  .event.left::before {{ right: -7.5px; }}
  .event.right::before {{ left: -7.5px; }}
  .card {{
    background: #fff; border-radius: 8px; padding: 1.25rem 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06);
    border: 1px solid #e2e8f0;
  }}
  .card-date {{
    font-size: 0.8rem; color: #6366f1; font-weight: 600; margin-bottom: 0.35rem;
  }}
  .card h3 {{ font-size: 1.05rem; margin-bottom: 0.5rem; color: #0f172a; }}
  .card p {{ font-size: 0.875rem; color: #475569; line-height: 1.5; }}
  .badge {{
    display: inline-block; font-size: 0.65rem; padding: 2px 8px;
    border-radius: 999px; font-weight: 600; margin-left: 0.5rem;
    vertical-align: middle;
  }}
  .badge.major {{ background: #fef3c7; color: #92400e; }}
  @media (max-width: 640px) {{
    .timeline::before {{ left: 1rem; }}
    .event {{ width: 100%; left: 0 !important; padding-left: 2.75rem !important; text-align: left !important; }}
    .event.left::before, .event.right::before {{ left: 0.35rem !important; }}
  }}
</style>
</head>
<body>
<h1>{self._escape_html(summary.data.get("title", page_title) if summary else page_title)}</h1>
<div class="timeline">{event_cards}
</div>
</body>
</html>"""

    # ------------------------------------------------------------------
    # Glossary HTML (Card grid + search)
    # ------------------------------------------------------------------

    def _to_glossary_html(
        self,
        parsed: ParsedContent,
        summary: Optional[SummaryResult],
    ) -> str:
        page_title = parsed.title or "Glossary"
        terms = self._get_data_field(summary, "terms", [])

        term_cards = ""
        for t in terms:
            term = self._escape_html(t.get("term", ""))
            definition = self._escape_html(t.get("definition", ""))
            category = self._escape_html(t.get("category", ""))
            related = ", ".join(t.get("related", []))
            related_html = ""
            if related:
                related_html = f'<div class="related"><span>关联:</span> {self._escape_html(related)}</div>'

            term_cards += f"""
    <div class="term-card" data-category="{category}">
      <div class="term-header">
        <h3>{term}</h3>
        <span class="cat-tag">{category}</span>
      </div>
      <p class="definition">{definition}</p>
      {related_html}
    </div>"""

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{self._escape_html(page_title)} — Glossary</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: #f8fafc; color: #1e293b; padding: 2rem;
  }}
  h1 {{ text-align: center; margin-bottom: 0.5rem; font-size: 1.75rem; color: #0f172a; }}
  .subtitle {{ text-align: center; margin-bottom: 1.5rem; color: #64748b; font-size: 0.9rem; }}
  .search-box {{
    max-width: 560px; margin: 0 auto 2rem;
  }}
  .search-box input {{
    width: 100%; padding: 0.75rem 1rem; border: 2px solid #e2e8f0;
    border-radius: 8px; font-size: 0.95rem; outline: none;
    transition: border-color 0.15s;
  }}
  .search-box input:focus {{ border-color: #6366f1; }}
  .filter-bar {{
    max-width: 560px; margin: 0 auto 1.5rem; display: flex;
    flex-wrap: wrap; gap: 0.5rem; justify-content: center;
  }}
  .filter-btn {{
    padding: 0.35rem 0.85rem; border: 1px solid #cbd5e1; border-radius: 999px;
    background: #fff; color: #475569; font-size: 0.8rem; cursor: pointer;
    transition: all 0.15s;
  }}
  .filter-btn:hover, .filter-btn.active {{
    background: #6366f1; color: #fff; border-color: #6366f1;
  }}
  .glossary-grid {{
    display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1rem; max-width: 1100px; margin: 0 auto;
  }}
  .term-card {{
    background: #fff; border-radius: 8px; padding: 1.25rem 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08); border: 1px solid #e2e8f0;
    transition: box-shadow 0.15s;
  }}
  .term-card:hover {{ box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
  .term-card.hidden {{ display: none; }}
  .term-header {{
    display: flex; justify-content: space-between; align-items: flex-start;
    margin-bottom: 0.5rem; gap: 0.5rem;
  }}
  .term-header h3 {{ font-size: 1.05rem; color: #0f172a; }}
  .cat-tag {{
    font-size: 0.7rem; padding: 2px 10px; border-radius: 999px;
    background: #eef2ff; color: #4338ca; font-weight: 500;
    white-space: nowrap;
  }}
  .definition {{
    font-size: 0.875rem; color: #475569; line-height: 1.5; margin-bottom: 0.5rem;
  }}
  .related {{
    font-size: 0.75rem; color: #94a3b8; padding-top: 0.5rem;
    border-top: 1px solid #f1f5f9;
  }}
  .related span {{ font-weight: 600; }}
  @media (max-width: 640px) {{
    .glossary-grid {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>
<h1>{self._escape_html(summary.data.get("title", page_title) if summary else page_title)}</h1>
<p class="subtitle">{len(terms)} 个术语</p>
<div class="search-box">
  <input type="text" id="search" placeholder="搜索术语..." oninput="filterTerms()">
</div>
<div class="filter-bar" id="filterBar"></div>
<div class="glossary-grid" id="grid">{term_cards}
</div>
<script>
(function() {{
  const cards = document.querySelectorAll('.term-card');
  const categories = [...new Set([...cards].map(c => c.dataset.category))].filter(Boolean).sort();

  const bar = document.getElementById('filterBar');
  let activeCat = '';
  function renderFilters() {{
    bar.innerHTML = '';
    const allBtn = document.createElement('button');
    allBtn.className = 'filter-btn' + (activeCat === '' ? ' active' : '');
    allBtn.textContent = '全部';
    allBtn.onclick = () => {{ activeCat = ''; filterTerms(); }};
    bar.appendChild(allBtn);
    categories.forEach(cat => {{
      const btn = document.createElement('button');
      btn.className = 'filter-btn' + (activeCat === cat ? ' active' : '');
      btn.textContent = cat;
      btn.onclick = () => {{ activeCat = cat; filterTerms(); }};
      bar.appendChild(btn);
    }});
  }}
  renderFilters();

  window.filterTerms = function() {{
    const q = (document.getElementById('search').value || '').toLowerCase();
    cards.forEach(card => {{
      const text = card.textContent.toLowerCase();
      const cat = card.dataset.category;
      const matchSearch = !q || text.includes(q);
      const matchCat = !activeCat || cat === activeCat;
      card.classList.toggle('hidden', !matchSearch || !matchCat);
    }});
    renderFilters();
  }};
}})();
</script>
</body>
</html>"""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_data_field(summary: Optional[SummaryResult], key: str, default=None):
        if summary and summary.data:
            return summary.data.get(key, default)
        return default

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

    @staticmethod
    def _escape_html(text: str) -> str:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

    @staticmethod
    def _escape_md(text: str) -> str:
        """Escape characters that could break markdown parsing inside Markmap."""
        return text.replace("\n", " ").replace("|", "\\|").replace("#", "\\#")
