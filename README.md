<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" />
  <img src="https://img.shields.io/badge/Status-Active-success?style=flat-square" />
</p>

<h1 align="center">WebDistill</h1>

<p align="center">
  <a href="README.md">English</a> | <a href="README.zh-CN.md">中文</a>
</p>

<p align="center"><strong>AI Web Intelligence & Distillation Framework</strong></p>

<p align="center">
An open-source pipeline for extracting, cleaning, and distilling structured knowledge from public web pages using AI.<br/>
Designed as infrastructure for developer workflows and agent systems.
</p>

---

## What It Does

WebDistill turns any public web page into clean, structured knowledge:

```
Public Web Page → Crawl → Clean → Parse → AI Summarize → Structured Output
```

It is **not** a web scraper. It is **AI information workflow infrastructure** — purpose-built for developers, researchers, and AI agents who need to transform raw HTML into distilled, machine-readable knowledge.

**Use cases:**
- Distill technical documentation into structured summaries
- Extract key insights from blog posts and articles
- Power AI agents with real-time web intelligence
- Build RAG knowledge bases from public web sources
- Automate content research and aggregation pipelines

## Architecture

```
                              WebDistill Pipeline
 ┌──────────────────────────────────────────────────────────────────────┐
 │                                                                      │
 │  URL ──▶ ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌───────────┐  │
 │          │ Crawler  │──▶│ Cleaner │──▶│ Parser  │──▶│ Summarizer│  │
 │          └─────────┘   └─────────┘   └─────────┘   └─────┬─────┘  │
 │               │              │              │               │        │
 │          requests +      bs4 + lxml     metadata       OpenAI API  │
 │          retry/UA        noise          extraction     structured  │
 │          timeout         removal                       JSON output  │
 │                                                         │        │
 │                                                    ┌────▼─────┐  │
 │                                                    │Formatter │  │
 │                                                    └────┬─────┘  │
 │                                                         │        │
 │                                                    Markdown /    │
 │                                                      JSON        │
 └──────────────────────────────────────────────────────────────────────┘
```

**Router** orchestrates the pipeline. Each stage is composable and replaceable.

## Features

- **Pipeline Architecture** — Crawl → Clean → Parse → Summarize → Format
- **Smart Cleaning** — Removes scripts, styles, navigation, ads to minimize token cost
- **AI Summarization** — OpenAI-powered structured extraction with JSON output
- **Multi-format Output** — Markdown and JSON
- **Task Routing** — Four modes: `default`, `technical`, `raw`, `full`
- **Agent-ready** — Clean interfaces designed for LangGraph, CrewAI, and MCP integration

## Quick Start

### Install

```bash
git clone https://github.com/your-org/WebDistill.git
cd WebDistill
pip install -r requirements.txt
export OPENAI_API_KEY="sk-..."
```

### CLI

```bash
# Default mode — full pipeline with AI summary
python main.py https://example.com/article

# Technical documentation mode
python main.py https://docs.python.org/3/library/asyncio.html --mode technical

# JSON output to file
python main.py https://example.com/article --format json --output result.json

# Raw mode — no AI, just extraction
python main.py https://example.com/article --mode raw --format markdown
```

### Library

```python
from router import Router

router = Router()
task = router.create_task(
    url="https://example.com/docs",
    mode="technical",
    output_format="json"
)
result = router.execute(task)

if result.ok:
    print(result.formatted_output.content)
    print(result.parsed_content.title)
    print(result.summary_result.key_points)
```

## Pipeline Modes

| Mode | Crawl | Clean | Parse | AI Summarize | Format |
|---|:---:|:---:|:---:|:---:|:---:|
| `default` | Yes | Yes | Yes | Yes | Yes |
| `technical` | Yes | Yes | Yes | Yes (tech prompt) | Yes |
| `raw` | Yes | Yes | Yes | **No** | Yes |
| `full` | Yes | Yes | Yes | Yes | Yes |

## Project Structure

```
WebDistill/
├── main.py              # CLI entry point
├── router.py            # Task routing & pipeline orchestration
├── crawler.py           # HTTP fetching with retry & UA rotation
├── cleaner.py           # HTML noise removal (scripts, styles, ads)
├── parser.py            # Content & metadata extraction
├── summarizer.py        # AI-powered structured summarization
├── formatter.py         # Output formatting (Markdown / JSON)
├── config/
│   └── settings.py      # Configuration management (dataclasses)
├── docs/
│   ├── architecture.md  # System architecture
│   ├── workflow.md      # Pipeline workflow details
│   └── roadmap.md       # Development roadmap
├── examples/
│   ├── basic_usage.py   # Basic usage examples
│   └── agent_workflow.py # Agent integration examples (LangGraph/CrewAI/MCP)
├── tests/
│   ├── test_crawler.py
│   ├── test_cleaner.py
│   ├── test_parser.py
│   └── test_formatter.py
├── skill/
│   └── SKILL.md         # Agent skill definition & safety rules
├── requirements.txt
├── LICENSE
├── README.md
└── README.zh-CN.md
```

## Roadmap

- [ ] Async crawling (aiohttp / httpx)
- [ ] Playwright rendering for JS-heavy pages
- [ ] LangGraph agent integration
- [ ] CrewAI multi-agent workflows
- [ ] MCP server protocol support
- [ ] RAG knowledge base integration
- [ ] Batch processing with job queue
- [ ] Plugin system for custom extractors

## License

MIT License. See [LICENSE](LICENSE).
