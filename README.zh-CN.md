<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" />
  <img src="https://img.shields.io/badge/Status-Active-success?style=flat-square" />
</p>

<h1 align="center">WebDistill</h1>

<p align="center">
  <a href="README.md">English</a> | <a href="README.zh-CN.md">中文</a>
</p>

<p align="center"><strong>AI 网页智能蒸馏框架</strong></p>

<p align="center">
从公开网页中提取、清洗、蒸馏结构化知识的开源流水线。<br/>
面向开发者、研究者和 AI Agent 的信息工作流基础设施。
</p>

---

## 它是什么

WebDistill 将任意公开网页转化为干净、结构化的知识：

```
公开网页 → 抓取 → 清洗 → 解析 → AI 总结 → 结构化输出
```

它**不是**爬虫。它是 **AI 信息工作流基础设施** —— 专为需要将原始 HTML 转化为可蒸馏、机器可读知识的开发者、研究者和 AI Agent 而设计。

**适用场景：**
- 将技术文档蒸馏为结构化摘要
- 从文章和博客中提取核心观点
- 为 AI Agent 提供实时网页智能
- 从公开网页构建 RAG 知识库
- 自动化内容研究与聚合流水线

## 架构

```
                           WebDistill 流水线
 ┌──────────────────────────────────────────────────────────────────────┐
 │                                                                      │
 │  URL ──▶ ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌───────────┐  │
 │          │ 抓取器    │──▶│ 清洗器   │──▶│ 解析器   │──▶│ AI 总结器  │  │
 │          │ Crawler  │   │ Cleaner │   │ Parser  │   │ Summarizer│  │
 │          └─────────┘   └─────────┘   └─────────┘   └─────┬─────┘  │
 │               │              │              │               │        │
 │          requests +      bs4 + lxml     元数据提取      OpenAI API │
 │          重试/UA         去噪去广告                     结构化 JSON │
 │          超时控制                                                  │
 │                                                         ▼        │
 │                                                    ┌──────────┐  │
 │                                                    │ 格式化器  │  │
 │                                                    │Formatter │  │
 │                                                    └────┬─────┘  │
 │                                                         │        │
 │                                                    Markdown /    │
 │                                                      JSON        │
 └──────────────────────────────────────────────────────────────────────┘
```

**Router（路由器）** 负责编排整个流水线。每个阶段可组合、可替换。

## 功能特性

- **流水线架构** — 抓取 → 清洗 → 解析 → 总结 → 格式化
- **智能清洗** — 去除脚本、样式、导航栏、广告，大幅减少 Token 消耗
- **AI 总结** — 基于 OpenAI API 的结构化提取，JSON 格式输出
- **多格式输出** — 支持 Markdown 和 JSON
- **任务路由** — 四种模式：`default`、`technical`、`raw`、`full`
- **Agent 就绪** — 预留 LangGraph、CrewAI、MCP 集成接口

## 快速开始

### 安装

```bash
git clone https://github.com/your-org/WebDistill.git
cd WebDistill
pip install -r requirements.txt
export OPENAI_API_KEY="sk-..."
```

### 命令行

```bash
# 默认模式 — 完整流水线 + AI 总结
python main.py https://example.com/article

# 技术文档模式
python main.py https://docs.python.org/3/library/asyncio.html --mode technical

# JSON 输出到文件
python main.py https://example.com/article --format json --output result.json

# 原始模式 — 不调用 AI，仅提取
python main.py https://example.com/article --mode raw --format markdown
```

### 作为库使用

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

## 流水线模式

| 模式 | 抓取 | 清洗 | 解析 | AI 总结 | 格式化 |
|---|:---:|:---:|:---:|:---:|:---:|
| `default` | Yes | Yes | Yes | Yes | Yes |
| `technical` | Yes | Yes | Yes | Yes（技术提示词） | Yes |
| `raw` | Yes | Yes | Yes | **否** | Yes |
| `full` | Yes | Yes | Yes | Yes | Yes |

## 项目结构

```
WebDistill/
├── main.py              # CLI 入口
├── router.py            # 任务路由 & 流水线编排
├── crawler.py           # HTTP 抓取（重试/UA/超时）
├── cleaner.py           # HTML 去噪（脚本/样式/广告）
├── parser.py            # 内容 & 元数据提取
├── summarizer.py        # AI 结构化总结
├── formatter.py         # 输出格式化（Markdown / JSON）
├── config/
│   └── settings.py      # 配置管理（dataclass）
├── docs/
│   ├── architecture.md  # 系统架构
│   ├── workflow.md      # 流水线工作流
│   └── roadmap.md       # 开发路线图
├── examples/
│   ├── basic_usage.py   # 基础用法示例
│   └── agent_workflow.py # Agent 集成示例（LangGraph/CrewAI/MCP）
├── tests/
│   ├── test_crawler.py
│   ├── test_cleaner.py
│   ├── test_parser.py
│   └── test_formatter.py
├── skill/
│   └── SKILL.md         # Agent 技能定义 & 安全规则
├── requirements.txt
├── LICENSE
├── README.md            # English
└── README.zh-CN.md      # 中文
```

## 路线图

- [ ] 异步抓取（aiohttp / httpx）
- [ ] Playwright 渲染 JS 重度页面
- [ ] LangGraph Agent 集成
- [ ] CrewAI 多 Agent 工作流
- [ ] MCP 服务端协议支持
- [ ] RAG 知识库集成
- [ ] 批量处理 & 任务队列
- [ ] 插件系统（自定义提取器）

## 许可证

MIT License. See [LICENSE](LICENSE).
