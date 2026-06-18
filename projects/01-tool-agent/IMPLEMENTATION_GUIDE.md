# 01-tool-agent 实现指南

这份文档带你从零实现一个最小工具调用 Agent。目标不是一开始就追求复杂框架，而是先理解 Agent 的核心闭环：

```text
用户输入
  -> Agent 判断是否需要工具
  -> 生成工具名和参数
  -> 程序执行工具
  -> 工具返回结构化结果
  -> Agent 整合成最终回答
```

当前项目提供的是一个本地 rule-based 版本，不需要 API Key。它把真实 LLM tool calling 中“模型选择工具”的部分先用规则模拟出来，方便你看清楚工具定义、工具执行、CLI 展示和测试评估的基本方式。理解之后，再把规则选择器替换成 LLM 即可。

## 1. 你最终会得到什么

完成后可以运行：

```powershell
tool-agent "帮我计算 23 * 17"
```

得到类似输出：

```text
用户输入：
帮我计算 23 * 17

工具调用：
- calculator({"expression": "23 * 17"})
  输出：391

最终回答：
计算结果：391
```

还可以运行：

```powershell
tool-agent --show-tools
```

查看当前暴露给 Agent 的工具 schema。

## 2. 环境配置

本项目统一使用 Conda 管理 Python 虚拟环境。为了后续所有 Agent 学习项目都能复用同一套基础环境，这里创建一个名为 `agent` 的 Conda 环境。

进入项目目录：

```powershell
cd "C:\研究生\z技能学习\Agent\projects\01-tool-agent"
```

确认已经安装 Conda：

```powershell
conda --version
```

创建名为 `agent` 的虚拟环境。建议使用 Python 3.12；如果你的机器暂时没有对应包，也可以改成 `python=3.11`：

```powershell
conda create -n agent python=3.12
```

激活虚拟环境：

```powershell
conda activate agent
```

确认当前 Python 来自 `agent` 环境：

```powershell
python --version
where python
```

升级 pip：

```powershell
python -m pip install --upgrade pip
```

以可编辑模式安装当前项目和开发依赖。可编辑模式的好处是：你修改 `src/tool_agent/` 下的代码后，不需要重新安装项目，命令行运行时会直接使用最新代码。

```powershell
python -m pip install -e ".[dev]"
```

安装完成后，推荐直接使用项目命令运行：

```powershell
tool-agent "帮我计算 23 * 17"
```

如果你暂时不想安装项目，也可以用临时方式运行：

```powershell
$env:PYTHONPATH="src"
python -m tool_agent.cli "帮我计算 23 * 17"
```

以后每次继续学习这个项目时，只需要进入项目目录并激活环境：

```powershell
cd "C:\研究生\z技能学习\Agent\projects\01-tool-agent"
conda activate agent
```

## 3. 项目结构

当前项目结构如下：

```text
projects/01-tool-agent/
  IMPLEMENTATION_GUIDE.md
  README.md
  FAILURES.md
  pyproject.toml
  src/
    tool_agent/
      __init__.py
      tools.py
      agent.py
      cli.py
  tests/
    test_tools.py
    test_agent.py
```

每个文件的职责：

- `pyproject.toml`：定义项目元信息、命令行入口和测试配置。
- `tools.py`：定义工具 schema、工具函数、工具注册表和统一执行入口。
- `agent.py`：实现最小 Agent loop，负责决定工具调用并生成最终回答。
- `cli.py`：命令行入口，负责接收用户输入、打印工具调用日志和最终回答。
- `tests/`：测试工具函数和 Agent 行为。
- `FAILURES.md`：记录失败样例，用于面试时讲优化过程。

## 4. 第一步：配置 pyproject.toml

`pyproject.toml` 让项目可以被安装，也让命令行里出现 `tool-agent` 命令。

核心配置：

```toml
[project]
name = "tool-agent"
version = "0.1.0"
description = "A minimal CLI tool-calling agent for learning agent loops."
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = [
  "pytest>=8.0.0",
]

[project.scripts]
tool-agent = "tool_agent.cli:main"

[tool.pytest.ini_options]
addopts = "-p no:cacheprovider"
pythonpath = ["src"]
testpaths = ["tests"]
```

重点理解：

- `dependencies = []` 表示运行项目不依赖第三方库。
- `dev` 里只有 `pytest`，用于测试。
- `tool-agent = "tool_agent.cli:main"` 表示安装后可以直接运行 `tool-agent`。
- `pythonpath = ["src"]` 让测试能找到 `src/tool_agent` 包。

## 5. 第二步：定义工具结果和工具规格

工具调用 Agent 的关键不是“函数能不能运行”，而是“函数能否被清楚地描述、调用、记录和评估”。

在 `src/tool_agent/tools.py` 中，先定义两个数据结构：

```python
@dataclass(frozen=True)
class ToolResult:
    name: str
    ok: bool
    input: dict[str, Any]
    output: Any | None = None
    error: str | None = None
```

`ToolResult` 是工具执行后的统一返回格式：

- `name`：工具名。
- `ok`：是否执行成功。
- `input`：本次工具收到的参数。
- `output`：成功时的结构化输出。
- `error`：失败时的错误说明。

再定义工具规格：

```python
@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., ToolResult]
```

`ToolSpec` 是工具暴露给 Agent 的说明书：

- `name`：工具的唯一名字，应该短、稳定、语义清楚。
- `description`：告诉 Agent 什么时候该用这个工具。描述写得好不好，直接决定模型 / 规则能否正确判断使用场景
- `parameters`：JSON Schema 风格的参数定义。
- `handler`：真正执行工具的 Python 函数。

这对应真实 LLM tool calling 的核心思想：模型不直接执行工具，它只根据工具说明生成“工具名 + 参数”；真正执行工具的是你的程序。

## 6. 第三步：实现 calculator 工具

计算器工具用于处理数学表达式。

不要直接使用 `eval()`，因为它可以执行任意 Python 代码。当前项目使用 `ast` 白名单，只允许数字和安全运算符。

简化版逻辑：

```python
def calculate(expression: str) -> ToolResult:
    expression = expression.strip() # 移除字符串首尾的空白字符
    tool_input = {"expression": expression}

    if not expression:
        return ToolResult("calculator", False, tool_input, error="表达式不能为空")

    try:
        tree = ast.parse(expression, mode="eval")
        value = _eval_math_node(tree)
    except ZeroDivisionError:
        return ToolResult("calculator", False, tool_input, error="除数不能为 0")
    except Exception as exc:
        return ToolResult("calculator", False, tool_input, error=str(exc))

    output: int | float = int(value) if value.is_integer() else value
    return ToolResult("calculator", True, tool_input, output=output)
```

关键点：

- 成功和失败都返回 `ToolResult`，不要让异常直接冲到 CLI。
- 工具要能独立测试，不依赖 Agent。
- 工具返回结构化结果，而不是一大段随意文本。

## 7. 第四步：实现 search_text 工具

文本搜索工具接收两个参数：

- `query`：要搜索的关键词。
- `text`：被搜索的文本。

返回结构：

```python
{
  "found": True,
  "count": 1,
  "matches": [
    {
      "index": 20,
      "snippet": "OpenAI Agents SDK 和 LangGraph 都可以做 Agent 编排。"
    }
  ]
}
```

这个工具体现了一个很重要的习惯：工具输出应尽量结构化。结构化输出更容易被日志记录、测试断言和后续模型总结。

## 8. 第五步：实现 get_current_time 工具

时间工具默认使用 `Asia/Shanghai`：

```python
def get_current_time(timezone_name: str = "Asia/Shanghai") -> ToolResult:
    timezone_name = timezone_name.strip() or "Asia/Shanghai"
    tool_input = {"timezone_name": timezone_name}
    ...
```

返回结构：

```python
{
  "timezone": "Asia/Shanghai",
  "date": "2026-06-16",
  "time": "14:30:00",
  "iso": "2026-06-16T14:30:00+08:00"
}
```

注意：Windows 上可能没有完整 IANA 时区数据库，所以代码里对 `Asia/Shanghai` 做了 UTC+8 兜底。

## 9. 第六步：注册工具

三个工具都实现后，需要放到统一注册表里：

```python
TOOL_REGISTRY: dict[str, ToolSpec] = {
    "calculator": ToolSpec(
        name="calculator",
        description="计算安全的数学表达式，只支持数字、括号和 + - * / % **。",
        parameters={...},
        handler=calculate,
    ),
    "search_text": ToolSpec(
        name="search_text",
        description="在给定文本中搜索关键词，返回是否命中、命中次数和片段。",
        parameters={...},
        handler=search_text,
    ),
    "get_current_time": ToolSpec(
        name="get_current_time",
        description="获取指定时区的当前日期和时间，默认使用 Asia/Shanghai。",
        parameters={...},
        handler=get_current_time,
    ),
}
```

注册表的作用：

- Agent 可以通过名字找到工具。
- CLI 可以打印工具 schema。
- 测试可以验证工具是否存在。
- 以后接入 LLM 时，可以把 `tool_schemas()` 传给模型。

统一执行入口：

```python
def run_tool(name: str, arguments: dict[str, Any]) -> ToolResult:
    spec = TOOL_REGISTRY.get(name)
    if spec is None:
        return ToolResult(name, False, arguments, error=f"未知工具：{name}")

    try:
        return spec.handler(**arguments)
    except TypeError as exc:
        return ToolResult(name, False, arguments, error=f"工具参数错误：{exc}")
```

这个函数很重要。真实项目里，所有工具调用都应该经过统一入口，方便做日志、权限、重试、超时和审计。

## 10. 第七步：实现 Agent loop

`src/tool_agent/agent.py` 中的 `RuleBasedToolAgent` 是本项目的核心。

它的主流程：

```python
class RuleBasedToolAgent:
    def run(self, user_input: str) -> AgentResponse:
        tool_calls = self._plan_tool_calls(user_input)
        tool_results = [
            run_tool(call.name, call.arguments)
            for call in tool_calls
        ]
        final_answer = self._compose_answer(user_input, tool_results)
        return AgentResponse(user_input, final_answer, tool_calls, tool_results)
```

你要重点看这三步：

1. `_plan_tool_calls()`：决定要不要调工具，以及调哪个工具。
2. `run_tool()`：执行工具。
3. `_compose_answer()`：把工具结果整理成用户能看懂的回答。

在真实 LLM Agent 中，第 1 步会交给模型；第 2 步永远由你的程序执行；第 3 步可以由模型或程序完成。

当前本地版本用规则模拟第 1 步：

- 看到“现在几点”“当前日期”，调用 `get_current_time`。
- 看到“在这段文本里搜索 xxx：yyy”，调用 `search_text`。
- 看到“计算 23 * 17”，调用 `calculator`。
- 其他问题不调用工具。

这就是最小 Agent loop。你理解这个闭环后，再学框架会轻松很多。

## 11. 第八步：实现 CLI

`src/tool_agent/cli.py` 负责三件事：

- 解析命令行参数。
- 调用 Agent。
- 打印工具调用日志和最终回答。

核心代码：

```python
def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.show_tools:
        print(json.dumps(tool_schemas(), ensure_ascii=False, indent=2))
        return

    agent = RuleBasedToolAgent()
    prompt = " ".join(args.prompt).strip()
    if prompt:
        _print_response(agent.run(prompt), as_json=args.json)
        return

    _interactive_loop(agent, as_json=args.json)
```

支持三种运行方式。

一次性输入：

```powershell
tool-agent "帮我计算 23 * 17"
```

JSON 输出：

```powershell
tool-agent --json "现在几点？"
```

调试流程输出：

```powershell
tool-agent --trace "帮我计算 23 * 17"
```

`--debug` 是 `--trace` 的别名：

```powershell
tool-agent --debug "在这段文本里搜索 LangGraph：OpenAI Agents SDK 和 LangGraph 都可以做 Agent 编排。"
```

交互模式：

```powershell
tool-agent
```

退出交互模式：

```text
exit
```

或者：

```text
quit
```

## 12. 第九步：运行测试

安装开发依赖后运行：

```powershell
python -m pytest
```

当前应该看到：

```text
11 passed
```

测试覆盖两类内容：

- `tests/test_tools.py`：验证单个工具是否正确。
- `tests/test_agent.py`：验证 Agent 是否选择了正确工具。

你后续每新增一个工具，都应该至少补两类测试：

- 工具函数的直接测试。
- Agent 是否会在合适场景调用它。

## 13. 第十步：手动运行几个例子

计算：

```powershell
tool-agent "帮我计算 23 * 17"
```

搜索：

```powershell
tool-agent "在这段文本里搜索 LangGraph：OpenAI Agents SDK 和 LangGraph 都可以做 Agent 编排。"
```

时间：

```powershell
tool-agent "现在几点？"
```

不需要工具的问题：

```powershell
tool-agent "请解释一下什么是 Agent loop"
```

查看工具 schema：

```powershell
tool-agent --show-tools
```

## 14. 如何理解 tools 的定义

一个工具不是随便写个函数就完了，它至少包含四层含义。

### 14.1 name

工具名要稳定，比如：

```text
calculator
search_text
get_current_time
```

不要使用含糊名字，比如：

```text
do_it
helper
tool1
```

模型和人都需要从名字判断工具用途。

### 14.2 description

description 是告诉 Agent “什么时候应该用这个工具”的。

好的描述：

```text
计算安全的数学表达式，只支持数字、括号和 + - * / % **。
```

不好的描述：

```text
很好用的计算工具。
```

后者无法帮助 Agent 判断适用场景。

### 14.3 parameters

parameters 描述工具需要哪些参数，类似函数签名的机器可读版本。

示例：

```python
{
    "type": "object",
    "properties": {
        "expression": {
            "type": "string",
            "description": "需要计算的数学表达式，例如 23 * 17。",
        }
    },
    "required": ["expression"],
    "additionalProperties": False,
}
```

关键点：

- 参数名要清楚。
- 必填字段要明确。
- `additionalProperties: False` 可以减少乱传参数。
- 每个参数最好都有 description。

### 14.4 handler

handler 是真正执行工具的函数：

```python
handler=calculate
```

真实项目中，handler 里可能会访问数据库、调用 API、读文件或执行搜索。无论多复杂，最好都返回统一的 `ToolResult`。

## 15. 本地规则 Agent 和真实 LLM Agent 的关系

本项目中：

```text
_plan_tool_calls()
```

负责决定工具调用。

真实 LLM tool calling 中，这一步通常变成：

```text
把用户输入 + 工具 schema 发给模型
  -> 模型返回 tool call
  -> 程序执行 tool call
  -> 把工具结果交回模型
  -> 模型生成最终回答
```

也就是说，你未来主要替换的是这一层：

```python
tool_calls = self._plan_tool_calls(user_input)
```

替换成模型返回的工具调用结果。

但这些部分不会变：

- 工具函数仍然要你自己实现。
- 工具 schema 仍然要你自己设计。
- 工具执行仍然在你的程序里发生。
- 工具失败仍然要处理。
- 工具调用日志仍然要保留。
- 测试和评估仍然要做。

## 16. 如何升级到真正的 LLM tool calling

升级时建议按这个顺序：

1. 保留 `tools.py` 的工具函数和 `TOOL_REGISTRY`。
2. 新建 `llm_agent.py`，不要一上来改掉本地规则版本。
3. 把 `tool_schemas()` 转成模型 API 需要的工具定义。
4. 把用户输入发送给模型。
5. 如果模型返回工具调用，就用 `run_tool(name, arguments)` 执行。
6. 把工具结果作为上下文交回模型。
7. 让模型生成最终回答。

概念伪代码：

```python
tools = tool_schemas()
model_response = call_model(user_input=user_input, tools=tools)

if model_response.has_tool_calls:
    for tool_call in model_response.tool_calls:
        result = run_tool(tool_call.name, tool_call.arguments)
        send_tool_result_back_to_model(tool_call.id, result.to_dict())

final_answer = ask_model_to_summarize()
```

注意：不同 API 和框架的参数格式会有差异。真正接入时应以官方文档为准。

推荐先看：

- OpenAI Function Calling：https://platform.openai.com/docs/guides/function-calling
- OpenAI Agents SDK：https://openai.github.io/openai-agents-python/

## 17. 学习时你应该观察什么

运行每个例子时，不要只看最终回答，要看这三件事：

1. 是否该调用工具。
2. 调用了哪个工具。
3. 工具参数是否正确。

例如：

```powershell
tool-agent --json "帮我计算 23 * 17"
```

观察输出里的：

```json
{
  "tool_calls": [
    {
      "name": "calculator",
      "arguments": {
        "expression": "23 * 17"
      }
    }
  ]
}
```

如果工具选错了，问题通常在“工具选择”。如果工具选对但结果错了，问题通常在“工具实现”。如果工具结果对但最终回答错了，问题通常在“结果整合”。

这个拆解方式是 Agent 调试的基本功。

## 18. 如何 debug 完整调用流程

本项目提供三种 debug 方式，从轻到重分别是普通输出、trace 输出、JSON 输出。

### 18.1 普通输出：看最终行为

适合快速确认 Agent 是否跑通：

```powershell
tool-agent "帮我计算 23 * 17"
```

你会看到：

```text
用户输入：
帮我计算 23 * 17

工具调用：
- calculator({"expression": "23 * 17"})
  输出：391

最终回答：
计算结果：391
```

普通输出适合回答这几个问题：

- 是否调用了工具？
- 调用了哪个工具？
- 最终回答是否合理？

### 18.2 trace 输出：看 Agent loop 每一步

适合学习和调试：

```powershell
tool-agent --trace "帮我计算 23 * 17"
```

输出会按阶段展示：

```text
=== Agent Trace ===

[1] input.received
收到用户输入。
{
  "user_input": "帮我计算 23 * 17"
}

[2] planning.completed
完成工具选择规划。
{
  "tool_call_count": 1,
  "tool_calls": [
    {
      "name": "calculator",
      "arguments": {
        "expression": "23 * 17"
      },
      "reason": "用户输入包含可计算的数学表达式。"
    }
  ]
}

[3] tool.started
开始执行工具 calculator。
...

[4] tool.completed
工具 calculator 执行完成。
...

[5] answer.completed
完成最终回答生成。
...
```

trace 输出对应代码里的流程：

```text
RuleBasedToolAgent.run()
  -> _plan_tool_calls()
  -> run_tool()
  -> _compose_answer()
```

每个 stage 的含义：

- `input.received`：CLI 收到用户输入，并交给 Agent。
- `planning.completed`：Agent 完成工具选择，决定是否调用工具。
- `tool.started`：程序准备执行某个工具。
- `tool.completed`：工具执行结束，返回 `ToolResult`。
- `answer.completed`：Agent 根据工具结果生成最终回答。

如果你想看搜索工具的完整流程：

```powershell
tool-agent --trace "在这段文本里搜索 LangGraph：OpenAI Agents SDK 和 LangGraph 都可以做 Agent 编排。"
```

如果你想看工具失败时的流程：

```powershell
tool-agent --trace "帮我计算 100 / 0"
```

重点观察 `tool.completed` 里的：

```json
{
  "name": "calculator",
  "ok": false,
  "input": {
    "expression": "100 / 0"
  },
  "output": null,
  "error": "除数不能为 0"
}
```

这说明工具没有抛出未处理异常，而是把错误包装成了结构化结果。真实 Agent 项目里，这一点很重要。

### 18.3 JSON 输出：看完整结构化数据

适合写测试、做评估、保存运行日志：

```powershell
tool-agent --json "帮我计算 23 * 17"
```

JSON 输出包含：

- `user_input`
- `final_answer`
- `tool_calls`
- `tool_results`
- `trace`

它适合被脚本读取。例如后续你可以写一个 eval 脚本，对 `evals/tool_agent_cases.jsonl` 里的样例逐条运行，然后统计工具选择准确率。

### 18.4 在代码里打断点

如果你使用 VS Code 或 PyCharm，建议在这几个位置打断点：

- `src/tool_agent/cli.py` 的 `main()`：看命令行参数如何进入程序。
- `src/tool_agent/agent.py` 的 `run()`：看 Agent loop 的主流程。
- `src/tool_agent/agent.py` 的 `_plan_tool_calls()`：看为什么选择某个工具。
- `src/tool_agent/tools.py` 的 `run_tool()`：看工具名和参数如何映射到 handler。
- `src/tool_agent/tools.py` 的 `calculate()` / `search_text()` / `get_current_time()`：看工具内部输入输出。

最推荐的断点顺序：

```text
cli.py main()
  -> agent.py RuleBasedToolAgent.run()
  -> agent.py _plan_tool_calls()
  -> tools.py run_tool()
  -> tools.py calculate()
  -> agent.py _compose_answer()
```

调试时请始终带着三个问题看代码：

1. 工具是否选对了？
2. 工具参数是否解析对了？
3. 工具结果是否被正确整合进最终回答？

## 19. 下一步练习

完成当前版本后，建议做 5 个小练习：

1. 给 `calculator` 增加对中文“加减乘除”的支持。
2. 给 `search_text` 增加大小写敏感开关。
3. 新增 `read_file(path: str)` 工具，但限制只能读取项目目录下的文件。
4. 用 `evals/tool_agent_cases.jsonl` 手动跑 20 条样例，记录成功率。
5. 把失败样例写入 `FAILURES.md`。

## 20. 面试表达

这个项目可以这样讲：

> 我实现了一个最小工具调用 Agent，用本地规则模拟模型的工具选择过程，重点理解 Agent loop。项目中我把工具抽象成 ToolSpec，包括 name、description、parameters 和 handler；工具统一返回 ToolResult，便于日志、错误处理和测试。CLI 会展示工具调用轨迹，所以能清楚区分工具选择错误、工具执行错误和最终回答错误。这个结构后续可以把规则选择器替换为 LLM tool calling。

面试官可能追问：

- 为什么不能直接 `eval()` 数学表达式？
- 工具 schema 的 description 写不好会有什么后果？
- 工具失败后应该返回异常还是结构化错误？
- 如果工具数量变多，如何减少模型选错工具？
- 为什么要把工具选择、工具执行、最终回答拆开？
