# 第一周学习计划：工具调用 Agent

周期：第 1 周

本周目标：做出一个可运行的 CLI 工具调用 Agent，理解 tool calling 的基本机制，并准备第一批评估样例。

## 本周交付物

- `projects/01-tool-agent`：项目目录和 README。
- 一个 CLI 程序：用户输入任务，Agent 决定是否调用工具。
- 至少 3 个工具：计算器、文本搜索、当前时间或文件摘要。
- `evals/tool_agent_cases.jsonl`：20 条测试样例。
- 一页失败记录：列出至少 3 个失败案例和改进方向。

## Day 1：理解 Agent 最小闭环

学习重点：

- Chat model、system instruction、user message 的角色。
- 什么是 tool calling。
- Agent loop：观察输入、选择工具、执行工具、整合结果。

要做的事：

- 阅读 `README.md` 和 `PROJECTS.md` 中项目 1 的要求。
- 在 `notes/` 下写一篇笔记：`2026-06-11-agent-basics.md`。
- 画出你理解的最小 Agent 流程：
  - 用户问题
  - 模型判断
  - 工具调用
  - 工具返回
  - 最终回答

验收标准：

- 你能用 3 分钟解释 tool calling 和普通聊天的区别。
- 你能说出工具 schema 为什么重要。

## Day 2：搭建 Python 项目

学习重点：

- Python 项目结构。
- 环境管理。
- 命令行入口。

要做的事：

- 在 `projects/01-tool-agent` 下初始化 Python 项目。
- 建议先用最小依赖，不急着上复杂框架。
- 写一个能运行的 CLI：
  - 输入：用户任务。
  - 输出：暂时可以是规则判断后的固定回答。

推荐结构：

```text
projects/01-tool-agent/
  README.md
  pyproject.toml
  src/tool_agent/
    __init__.py
    cli.py
    agent.py
    tools.py
  tests/
    test_tools.py
```

验收标准：

- 能运行 `python -m tool_agent.cli` 或等价命令。
- 至少有一个测试能通过。

## Day 3：实现 3 个本地工具

学习重点：

- 工具函数的输入输出设计。
- 参数校验。
- 错误返回。

要做的事：

- 实现 `calculator(expression: str)`。
- 实现 `search_text(query: str, text: str)`。
- 实现 `get_current_time()` 或 `summarize_file(path: str)`。

验收标准：

- 工具函数可以脱离模型单独测试。
- 错误输入不会让程序崩溃。
- 每个工具都有清晰的返回结构。

## Day 4：接入 LLM 工具调用

学习重点：

- 如何把工具描述给模型。
- 如何解析模型发起的工具调用。
- 如何把工具结果再交给模型整合。

要做的事：

- 选择一种实现方式：
  - 简单方式：直接用 OpenAI API 的工具调用能力。
  - 框架方式：用 OpenAI Agents SDK 做最小 Agent。
- 把 Day 3 的 3 个工具暴露给模型。
- 在 CLI 中打印工具调用日志。

验收标准：

- 输入“帮我算 23 * 17”时，会调用计算器。
- 输入不需要工具的问题时，不乱调用工具。
- 工具失败时，最终回答能说明失败原因。

## Day 5：补测试和评估样例

学习重点：

- 单元测试和端到端评估的区别。
- 如何设计 Agent 测试集。

要做的事：

- 使用 `evals/tool_agent_cases.jsonl` 的 20 条样例跑一遍。
- 记录每条样例是否成功。
- 把失败样例写进 `projects/01-tool-agent/FAILURES.md`。

验收标准：

- 至少 20 条评估样例。
- 记录工具选择准确率。
- 至少 3 个失败案例有分析。

## Day 6：整理项目表达

学习重点：

- 把代码变成面试项目。
- 从需求、架构、难点、指标讲清楚项目。

要做的事：

- 完善 `projects/01-tool-agent/README.md`。
- 写一个 3 分钟项目讲稿，放到 `interview/01-tool-agent-talk.md`。
- 准备 5 个面试追问。

验收标准：

- 不看代码也能讲清项目。
- 能说出 2 个设计取舍。
- 能解释一个失败案例和修复思路。

## Day 7：复盘和下周准备

学习重点：

- 复盘比多学更重要。
- 下周进入 RAG 前，要先搞清楚本周 Agent 的短板。

要做的事：

- 汇总本周成功率、失败类型、代码遗留问题。
- 列出下周 RAG 项目需要准备的资料。
- 整理 3 个你还没想明白的问题。

验收标准：

- 有一份本周复盘。
- 项目可以从零运行。
- 你能明确说出下一周为什么要学 RAG。

## 今天立刻做

1. 先完成 Day 1。
2. 写下 5 个你希望 Agent 会调用工具解决的问题。
3. 明天再开始写代码。

