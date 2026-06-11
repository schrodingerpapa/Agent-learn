# Agent 学习仓库

这个目录用于在 2026-06-11 到 2026-09-11 之间，快速建立 Agent 开发能力，并沉淀可用于秋招面试的项目作品。

## 目标

三个月后达到“能讲清楚、能写出来、能上线演示、能解释取舍”的水平。

核心能力画像：

- LLM 应用基础：Prompt、结构化输出、函数调用、流式响应、成本与延迟控制。
- Agent 核心机制：工具调用、规划与执行、状态管理、记忆、Human-in-the-loop、失败恢复。
- RAG 与知识工程：文档解析、切分、Embedding、向量检索、重排、引用、评估。
- Agent 工程化：FastAPI 服务、任务队列、日志追踪、配置管理、测试、部署。
- 生态理解：OpenAI Agents SDK、LangGraph、AutoGen、MCP 的适用场景和差异。
- 面试表达：能从需求、架构、关键代码、评估指标、失败案例、优化方案完整讲项目。

## 推荐学习主线

优先级从高到低：

1. Python 工程基础：`asyncio`、类型标注、Pydantic、FastAPI、pytest。
2. LLM API 与工具调用：结构化输出、函数工具、工具 schema、异常处理。
3. RAG：从本地 Markdown/PDF 知识库开始，做到带引用和可评估。
4. Agent Runtime：用 OpenAI Agents SDK 或 LangGraph 做状态化、多步骤工作流。
5. MCP：写一个本地 MCP server，把你的工具标准化暴露给 Agent。
6. Eval/Observability：为每个项目准备测试集、日志、trace、指标面板或报告。

## 仓库建议结构

```text
Agent/
  README.md
  ROADMAP_90_DAYS.md
  PROJECTS.md
  notes/
  experiments/
  projects/
    01-tool-agent/
    02-rag-assistant/
    03-mcp-server/
    04-capstone-agent/
  evals/
  interview/
```

## 每周节奏

- 周一到周四：学习一个主题并写最小 demo。
- 周五：把 demo 工程化，补 README、测试和日志。
- 周六：复盘失败案例，整理面试表达。
- 周日：轻量刷题、补基础、看优秀项目源码。

## 产出标准

每个项目至少包含：

- 一页 README：问题背景、架构图、运行方式、关键技术、效果截图或日志。
- 可运行 demo：CLI、Web API 或简单前端均可。
- 评估集：至少 20 条典型输入和期望行为。
- 失败分析：列出 3 个失败案例和改进方案。
- 简历 bullet：用 STAR 方式描述结果和指标。

## 参考资料

- OpenAI Agents SDK：https://openai.github.io/openai-agents-python/
- LangGraph：https://docs.langchain.com/oss/python/langgraph/overview
- AutoGen AgentChat：https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/index.html
- Model Context Protocol：https://modelcontextprotocol.io/docs/getting-started/intro
