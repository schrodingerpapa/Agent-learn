# 项目一掌握判断清单

本清单用于判断你是否真正掌握了 `01-tool-agent`。重点不是是否把所有代码手动敲了一遍，而是是否能解释、修改、扩展、调试和复现核心调用链路。

## 是否必须手动敲完整个项目

不必须。

机械重敲一遍代码不等于掌握。更有效的学习方式是：

1. 读懂整体结构。
2. 能跑通项目。
3. 能解释关键流程。
4. 能独立新增一个小工具。
5. 能根据 trace 定位问题。
6. 能把项目讲成面试项目。

如果时间充足，可以手动重写 `tools.py` 和 `agent.py` 的核心部分；如果时间紧，更建议做“新增工具 + 补测试 + 跑 trace”的练习。

## 掌握标准 1：能讲清 Agent loop

你应该能不看代码说清楚这个流程：

```text
用户输入
  -> Agent 判断是否需要工具
  -> 生成工具名和参数
  -> run_tool 执行工具
  -> ToolResult 返回结构化结果
  -> Agent 整合最终回答
```

你还应该能说明三个核心文件的职责：

- `tools.py`：定义工具、工具 schema、工具注册表和统一执行入口。
- `agent.py`：实现 Agent loop，负责工具选择、工具执行编排和回答整合。
- `cli.py`：接收命令行输入，调用 Agent，展示工具调用日志、trace 或 JSON。

自测问题：

- Tool calling 和普通聊天有什么区别？
- 为什么工具执行必须由程序完成，而不是由模型完成？
- 为什么工具返回值要结构化？

## 掌握标准 2：能读懂 trace

运行：

```powershell
python -m tool_agent.cli --trace "帮我计算 23 * 17"
```

你应该能解释每个阶段：

```text
input.received
planning.completed
tool.started
tool.completed
answer.completed
```

每个阶段的含义：

- `input.received`：收到用户输入。
- `planning.completed`：完成工具选择规划。
- `tool.started`：开始执行工具。
- `tool.completed`：工具执行完成，返回 `ToolResult`。
- `answer.completed`：根据工具结果生成最终回答。

你应该能根据 trace 判断问题出现在哪一层：

- 工具没有被调用：检查 `_plan_tool_calls()`。
- 工具选错了：检查工具选择规则或工具描述。
- 工具参数错了：检查参数解析逻辑。
- 工具结果错了：检查具体工具函数。
- 工具结果正确但回答错了：检查 `_compose_answer()`。

## 掌握标准 3：能独立新增一个工具

建议练习：新增 `word_count(text: str)` 工具。

目标行为：

```text
输入：统计这段文本的字数：Agent 开发需要工具调用和评估
工具：word_count
输出：字符数、词数或中英文混合统计结果
```

你需要完成：

1. 在 `tools.py` 中实现 `word_count` handler。
2. 定义 `ToolSpec`，包括 `name`、`description`、`parameters`、`handler`。
3. 把工具加入 `TOOL_REGISTRY`。
4. 在 `agent.py` 中增加触发规则。
5. 在 `tests/` 中补工具测试和 Agent 测试。
6. 用 CLI 跑通普通输出、`--trace` 和 `--json`。

如果你能完成这个练习，说明你已经理解了工具调用 Agent 的主要结构。

## 掌握标准 4：能修复一个失败案例

你应该能故意制造或找到一个失败案例，并完成分析。

例子：

```powershell
python -m tool_agent.cli --trace "请计算 15% 的 240"
```

如果结果不符合预期，你应该能顺着下面的顺序定位：

```text
agent.py _extract_math_expression()
  -> agent.py _plan_tool_calls()
  -> tools.py run_tool()
  -> tools.py calculate()
  -> agent.py _compose_answer()
```

失败案例记录格式：

```text
用户输入：

期望行为：

实际行为：

原因分析：

改进方案：
```

至少完成 3 个失败案例，写入 `FAILURES.md`。

## 掌握标准 5：能说明如何升级到真实 LLM tool calling

你不一定要马上接入 OpenAI API，但应该能解释清楚：

当前项目中：

```python
tool_calls = self._plan_tool_calls(user_input)
```

是本地规则模拟工具选择。

真实 LLM tool calling 中，这一步会变成：

```text
把用户输入和 tool schema 发给模型
  -> 模型返回工具名和参数
  -> 程序调用 run_tool(name, arguments)
  -> 把工具结果交回模型
  -> 模型生成最终回答
```

升级时不应该推翻整个项目，因为这些部分仍然保留：

- `tools.py` 中的工具函数。
- `ToolSpec` 和参数 schema。
- `run_tool()` 统一执行入口。
- `ToolResult` 结构化返回。
- trace/debug 日志。
- 测试和评估样例。

## 最小掌握练习

你可以按下面顺序验收自己：

1. 画出 Agent loop。
2. 跑通：

```powershell
python -m tool_agent.cli --trace "帮我计算 23 * 17"
```

3. 解释 trace 中每个阶段。
4. 新增一个 `word_count` 工具。
5. 给新工具补测试。
6. 故意制造一个失败案例并修复。
7. 用 3 分钟讲清楚项目。

完成这 7 步，就可以认为你已经掌握项目一的核心。

## 面试版表达

可以这样说：

> 我通过 `01-tool-agent` 掌握了工具调用 Agent 的基本结构。项目中我把工具抽象成 `ToolSpec`，包含工具名、描述、参数 schema 和 handler；工具执行统一返回 `ToolResult`，方便记录日志、处理错误和测试。Agent loop 负责根据输入规划工具调用、执行工具、整合结果，并通过 `--trace` 展示完整调用链路。这个项目目前用本地规则模拟模型选择工具，但结构上可以平滑替换为真实 LLM tool calling。

## 最终判断

如果你只是能运行项目，还不算掌握。

如果你能做到以下几点，就算掌握：

- 能讲清 Agent loop。
- 能读懂 trace。
- 能新增一个工具。
- 能补测试。
- 能修失败案例。
- 能解释如何升级到 LLM tool calling。
- 能把项目讲成面试项目。

