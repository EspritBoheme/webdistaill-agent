# WebDistill

**AI Web Intelligence & Distillation Framework**

WebDistill is a modular pipeline for extracting, cleaning, and distilling structured knowledge from public web pages using AI. Designed as infrastructure for developer workflows and agent systems.

## Features

- **Pipeline Architecture** — Crawl → Clean → Parse → Summarize → Format
- **Smart Cleaning** — Removes noise (scripts, styles, nav, ads) to minimize token consumption
- **AI Summarization** — OpenAI-powered structured extraction
- **Multi-format Output** — Markdown and JSON
- **Task Routing** — Automatic pipeline selection based on content type
- **Agent-ready** — Clean interfaces for LangGraph, CrewAI, and MCP integration

## Architecture

```
URL Input
   │
   ▼
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌───────────┐    ┌───────────┐
│ Crawler  │───▶│ Cleaner │───▶│ Parser  │───▶│ Summarizer│───▶│ Formatter │
└─────────┘    └─────────┘    └─────────┘    └───────────┘    └───────────┘
   │               │               │               │               │
 requests      bs4 + lxml      metadata       OpenAI API      MD / JSON
 retry/UA       noise removal   extraction     structured      output
```

## Workflow

```
1. Router receives URL + task config
2. Crawler fetches raw HTML (with retry, UA rotation)
3. Cleaner strips noise elements
4. Parser extracts title, content, metadata
5. Summarizer produces AI-structured summary
6. Formatter renders final output
```

## Installation

```bash
git clone https://github.com/your-org/WebDistill.git
cd WebDistill
pip install -r requirements.txt
```

Set your OpenAI API key:

```bash
export OPENAI_API_KEY="sk-..."
```

## Usage

### Basic

```bash
python main.py https://example.com/article
```

### With options

```bash
python main.py https://example.com/article --format json --output result.json
python main.py https://example.com/article --format markdown --output result.md
python main.py https://example.com/docs --mode technical --format markdown
```

### As a library

```python
from crawler import Crawler
from cleaner import Cleaner
from parser import ContentParser
from summarizer import Summarizer
from formatter import Formatter

pipeline = Pipeline()\
    .pipe(Crawler())\
    .pipe(Cleaner())\
    .pipe(ContentParser())\
    .pipe(Summarizer())\
    .pipe(Formatter(output_format="markdown"))

result = pipeline.run("https://example.com/article")
```

### Agent workflow

```python
from router import Router

router = Router()
task = router.create_task(
    url="https://example.com/docs",
    mode="technical",
    output_format="json"
)
result = router.execute(task)
```

## Project Structure

```
WebDistill/
├── main.py              # CLI entry point
├── router.py            # Task routing & pipeline orchestration
├── crawler.py           # HTTP fetching with retry & UA rotation
├── cleaner.py           # HTML noise removal
├── parser.py            # Content & metadata extraction
├── summarizer.py        # AI-powered summarization
├── formatter.py         # Output formatting (MD/JSON)
├── config/
│   └── settings.py      # Configuration management
├── docs/
│   ├── architecture.md  # System architecture
│   ├── workflow.md      # Pipeline workflow
│   └── roadmap.md       # Development roadmap
├── examples/
│   ├── basic_usage.py   # Basic usage examples
│   └── agent_workflow.py # Agent integration examples
├── tests/
│   ├── test_crawler.py
│   ├── test_cleaner.py
│   ├── test_parser.py
│   └── test_formatter.py
├── skill/
│   └── SKILL.md         # Agent skill definition
├── requirements.txt
├── LICENSE
└── README.md
```

## Roadmap

- [ ] Async crawling (aiohttp / httpx)
- [ ] Playwright rendering for JS-heavy pages
- [ ] LangGraph agent integration
- [ ] CrewAI multi-agent workflows
- [ ] MCP server protocol support
- [ ] RAG knowledge base integration
- [ ] Batch processing with job queue
- [ ] Content deduplication
- [ ] Multi-language support
- [ ] Plugin system for custom extractors

## Future Plans

**Phase 2** — Agent Infrastructure
- MCP-compatible tool interface
- LangGraph stateful workflows
- CrewAI agent delegation

**Phase 3** — Knowledge System
- RAG-backed knowledge base
- Vector store integration
- Semantic search over distilled content

**Phase 4** — Multi-Agent Orchestration
- Research agent swarm
- Cross-source synthesis
- Automated report generation

## License

MIT License. See [LICENSE](LICENSE).
