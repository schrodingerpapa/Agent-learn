# 90 天 Agent 开发路线图

周期：2026-06-11 到 2026-09-11。

策略：先做能跑通的 Agent，再补工程化和评估。秋招更看重“你是否理解 Agent 为什么会失败、如何定位、如何改进”，不只是会调库。

## 第 1 阶段：入门闭环，能写出最小 Agent

时间：第 1-2 周

目标：

- 搭好 Python 开发环境：`uv` 或 `conda`、FastAPI、pytest、ruff、pre-commit。
- 掌握 LLM API 基础：messages、system/developer 指令、JSON schema、streaming。
- 写出第一个工具调用 Agent：天气/计算器/文件检索/网页摘要任选。

交付物：

- `projects/01-tool-agent`：一个 CLI Agent，可以选择工具、调用工具、返回结构化结果。
- 20 条测试问题，覆盖正常输入、模糊输入、工具失败、无权限场景。

面试要会讲：

- Tool calling 和普通 chat completion 的区别。
- 为什么工具描述、参数 schema、错误返回会影响 Agent 表现。
- 如何避免 Agent 乱调用工具。

## 第 2 阶段：RAG，做一个“能引用证据”的知识库助手

时间：第 3-5 周

目标：

- 掌握文档加载、切分、Embedding、向量检索、重排、上下文压缩。
- 做到回答带引用，不能回答时明确拒答。
- 建立最小评估集：检索命中率、答案相关性、faithfulness、延迟、成本。

交付物：

- `projects/02-rag-assistant`：面向你的学习笔记或论文资料的 RAG 助手。
- `evals/rag_eval.jsonl`：不少于 50 条问答样本。
- 一份 `RAG_FAILURES.md`：记录幻觉、漏检、切分错误、上下文过长等问题。

面试要会讲：

- chunk size、overlap、top-k、rerank 的取舍。
- RAG 为什么仍然会幻觉。
- 如何从 trace 判断是检索错了，还是生成错了。

## 第 3 阶段：Agent 编排，掌握状态、分支和多步任务

时间：第 6-8 周

目标：

- 学 OpenAI Agents SDK 或 LangGraph，理解 agent loop、handoff、state、checkpoint。
- 做一个多步骤任务：研究助手、代码审查助手、简历优化助手、数据分析助手任选。
- 加入 Human-in-the-loop：关键步骤需要用户确认或修改状态。

交付物：

- `projects/04-capstone-agent` 的第一版：能完成一个真实多步工作流。
- Trace 日志或运行记录：至少 10 次完整任务执行。
- 错误恢复机制：工具失败、模型输出格式错误、超时、无相关资料。

面试要会讲：

- Workflow 和 Agent 的边界：什么时候写死流程，什么时候交给模型决策。
- 多 Agent 是否必要，如何避免复杂度失控。
- 状态持久化、重试、幂等性为什么重要。

## 第 4 阶段：MCP 与工程化，做成可复用工具

时间：第 9-10 周

目标：

- 理解 MCP 的 server/client/tools/resources/prompts。
- 写一个本地 MCP server，比如：学习笔记检索、简历项目库查询、GitHub issue 分析。
- 将 Agent 接入 MCP 工具，展示“工具可被不同客户端复用”。

交付物：

- `projects/03-mcp-server`：一个可运行 MCP server。
- 接入文档：工具列表、输入输出 schema、权限边界、失败返回。

面试要会讲：

- MCP 解决了什么问题，和普通 REST API 的区别是什么。
- 工具权限、提示注入、数据泄露风险如何处理。
- Tool schema 设计对 Agent 性能的影响。

## 第 5 阶段：作品集冲刺与面试准备

时间：第 11-12 周

目标：

- 选择 1 个主项目打磨到可展示水平，另外 2 个小项目作为能力补充。
- 为主项目补齐测试、评估、部署、README、架构图、演示视频或截图。
- 准备面试问答：项目深挖、系统设计、算法基础、Python 工程基础。

交付物：

- 一份主项目 README。
- 一份项目复盘：背景、难点、方案、指标、失败、优化。
- 一份简历项目描述。
- 一份 30 分钟面试讲稿。

面试要会讲：

- 你的 Agent 和普通 LLM 应用相比强在哪里。
- 你做过哪些评估，指标怎么定义。
- 如果用户量扩大 10 倍，系统瓶颈在哪里。
- 如果模型输出不稳定，你如何定位和修复。

## 每周固定检查点

- 本周是否有一个可运行 demo。
- 是否写了 README 和运行命令。
- 是否有测试样例或 eval 样本。
- 是否记录至少 3 个失败案例。
- 是否能用 3 分钟讲清楚本周项目。

