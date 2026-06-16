from __future__ import annotations

import ast
import operator
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


@dataclass(frozen=True)
class ToolResult:
    name: str
    ok: bool
    input: dict[str, Any]
    output: Any | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "ok": self.ok,
            "input": self.input,
            "output": self.output,
            "error": self.error,
        }


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., ToolResult]

    def schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "strict": True,
        }


_BIN_OPS: dict[type[ast.operator], Callable[[float, float], float]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARY_OPS: dict[type[ast.unaryop], Callable[[float], float]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _eval_math_node(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval_math_node(node.body)

    if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
        return float(node.value)

    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_eval_math_node(node.operand))

    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        left = _eval_math_node(node.left)
        right = _eval_math_node(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 10:
            raise ValueError("指数过大，已拒绝计算")
        return _BIN_OPS[type(node.op)](left, right)

    raise ValueError("只支持数字、括号和 + - * / % ** 运算")


def calculate(expression: str) -> ToolResult:
    expression = expression.strip()
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


def search_text(query: str, text: str) -> ToolResult:
    query = query.strip()
    text = text.strip()
    tool_input = {"query": query, "text": text}

    if not query:
        return ToolResult("search_text", False, tool_input, error="搜索关键词不能为空")

    query_lower = query.lower()
    text_lower = text.lower()
    matches: list[dict[str, Any]] = []
    start = 0

    while True:
        index = text_lower.find(query_lower, start)
        if index == -1:
            break
        snippet_start = max(0, index - 20)
        snippet_end = min(len(text), index + len(query) + 20)
        matches.append(
            {
                "index": index,
                "snippet": text[snippet_start:snippet_end],
            }
        )
        start = index + len(query)

    return ToolResult(
        "search_text",
        True,
        tool_input,
        output={
            "found": bool(matches),
            "count": len(matches),
            "matches": matches,
        },
    )


def _load_timezone(name: str) -> timezone | ZoneInfo:
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        if name in {"Asia/Shanghai", "UTC+08:00", "+08:00"}:
            return timezone(timedelta(hours=8), name="Asia/Shanghai")
        if name in {"UTC", "Etc/UTC"}:
            return timezone.utc
        raise


def get_current_time(timezone_name: str = "Asia/Shanghai") -> ToolResult:
    timezone_name = timezone_name.strip() or "Asia/Shanghai"
    tool_input = {"timezone_name": timezone_name}

    try:
        tz = _load_timezone(timezone_name)
    except Exception:
        return ToolResult(
            "get_current_time",
            False,
            tool_input,
            error=f"未知时区：{timezone_name}",
        )

    now = datetime.now(tz)
    return ToolResult(
        "get_current_time",
        True,
        tool_input,
        output={
            "timezone": timezone_name,
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "iso": now.isoformat(timespec="seconds"),
        },
    )


TOOL_REGISTRY: dict[str, ToolSpec] = {
    "calculator": ToolSpec(
        name="calculator",
        description="计算安全的数学表达式，只支持数字、括号和 + - * / % **。",
        parameters={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "需要计算的数学表达式，例如 23 * 17。",
                }
            },
            "required": ["expression"],
            "additionalProperties": False,
        },
        handler=calculate,
    ),
    "search_text": ToolSpec(
        name="search_text",
        description="在给定文本中搜索关键词，返回是否命中、命中次数和片段。",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "要搜索的关键词。",
                },
                "text": {
                    "type": "string",
                    "description": "被搜索的文本。",
                },
            },
            "required": ["query", "text"],
            "additionalProperties": False,
        },
        handler=search_text,
    ),
    "get_current_time": ToolSpec(
        name="get_current_time",
        description="获取指定时区的当前日期和时间，默认使用 Asia/Shanghai。",
        parameters={
            "type": "object",
            "properties": {
                "timezone_name": {
                    "type": "string",
                    "description": "IANA 时区名称，例如 Asia/Shanghai 或 UTC。",
                }
            },
            "required": ["timezone_name"],
            "additionalProperties": False,
        },
        handler=get_current_time,
    ),
}


def tool_schemas() -> list[dict[str, Any]]:
    return [tool.schema() for tool in TOOL_REGISTRY.values()]


def run_tool(name: str, arguments: dict[str, Any]) -> ToolResult:
    spec = TOOL_REGISTRY.get(name)
    if spec is None:
        return ToolResult(name, False, arguments, error=f"未知工具：{name}")

    try:
        return spec.handler(**arguments)
    except TypeError as exc:
        return ToolResult(name, False, arguments, error=f"工具参数错误：{exc}")

