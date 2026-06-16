from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .tools import ToolResult, run_tool


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict[str, Any]
    reason: str


@dataclass(frozen=True)
class TraceStep:
    stage: str
    message: str
    data: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "message": self.message,
            "data": self.data,
        }


@dataclass(frozen=True)
class AgentResponse:
    user_input: str
    final_answer: str
    tool_calls: list[ToolCall]
    tool_results: list[ToolResult]
    trace: list[TraceStep]

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_input": self.user_input,
            "final_answer": self.final_answer,
            "tool_calls": [
                {
                    "name": call.name,
                    "arguments": call.arguments,
                    "reason": call.reason,
                }
                for call in self.tool_calls
            ],
            "tool_results": [result.to_dict() for result in self.tool_results],
            "trace": [step.to_dict() for step in self.trace],
        }


class RuleBasedToolAgent:
    """A tiny local agent loop for learning tool calling without an API key."""

    def run(self, user_input: str) -> AgentResponse:
        trace = [
            TraceStep(
                "input.received",
                "收到用户输入。",
                {"user_input": user_input},
            )
        ]

        tool_calls = self._plan_tool_calls(user_input)
        trace.append(
            TraceStep(
                "planning.completed",
                "完成工具选择规划。",
                {
                    "tool_call_count": len(tool_calls),
                    "tool_calls": [
                        {
                            "name": call.name,
                            "arguments": call.arguments,
                            "reason": call.reason,
                        }
                        for call in tool_calls
                    ],
                },
            )
        )

        tool_results: list[ToolResult] = []
        for call in tool_calls:
            trace.append(
                TraceStep(
                    "tool.started",
                    f"开始执行工具 {call.name}。",
                    {
                        "name": call.name,
                        "arguments": call.arguments,
                    },
                )
            )
            result = run_tool(call.name, call.arguments)
            tool_results.append(result)
            trace.append(
                TraceStep(
                    "tool.completed",
                    f"工具 {call.name} 执行完成。",
                    result.to_dict(),
                )
            )

        final_answer = self._compose_answer(user_input, tool_results)
        trace.append(
            TraceStep(
                "answer.completed",
                "完成最终回答生成。",
                {"final_answer": final_answer},
            )
        )

        return AgentResponse(user_input, final_answer, tool_calls, tool_results, trace)

    def _plan_tool_calls(self, user_input: str) -> list[ToolCall]:
        if self._looks_like_time_question(user_input):
            return [
                ToolCall(
                    "get_current_time",
                    {"timezone_name": "Asia/Shanghai"},
                    "用户询问当前时间或日期，需要读取实时上下文。",
                )
            ]

        search_args = self._extract_search_args(user_input)
        if search_args is not None:
            return [
                ToolCall(
                    "search_text",
                    search_args,
                    "用户要求在给定文本中搜索关键词。",
                )
            ]

        expression = self._extract_math_expression(user_input)
        if expression is not None:
            return [
                ToolCall(
                    "calculator",
                    {"expression": expression},
                    "用户输入包含可计算的数学表达式。",
                )
            ]

        return []

    @staticmethod
    def _looks_like_time_question(user_input: str) -> bool:
        return any(
            keyword in user_input
            for keyword in ["现在几点", "当前时间", "当前日期", "今天日期", "现在时间"]
        )

    @staticmethod
    def _extract_search_args(user_input: str) -> dict[str, str] | None:
        patterns = [
            r"在这段文本里(?:搜索|查找|找)\s*(?P<query>.+?)[：:]\s*(?P<text>.+)",
            r"(?:搜索|查找)关键词\s*(?P<query>.+?)[：:]\s*(?P<text>.+)",
            r"在文本\s*(?P<text>.+?)\s*里(?:搜索|查找|找)\s*(?P<query>.+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, user_input)
            if match:
                return {
                    "query": match.group("query").strip(),
                    "text": match.group("text").strip(),
                }

        return None

    @staticmethod
    def _extract_math_expression(user_input: str) -> str | None:
        percent_match = re.search(
            r"(?P<percent>\d+(?:\.\d+)?)\s*%\s*的\s*(?P<base>\d+(?:\.\d+)?)",
            user_input,
        )
        if percent_match:
            percent = percent_match.group("percent")
            base = percent_match.group("base")
            return f"({percent} / 100) * {base}"

        power_match = re.search(
            r"(?P<base>\d+(?:\.\d+)?)\s*的\s*(?P<power>\d+)\s*次方",
            user_input,
        )
        if power_match:
            base = power_match.group("base")
            power = power_match.group("power")
            return f"{base} ** {power}"

        after_calculate = re.search(
            r"(?:计算|算一下|算|calculate)\s*(?P<expr>[^，。！？?,]+)",
            user_input,
            flags=re.IGNORECASE,
        )
        if after_calculate:
            return after_calculate.group("expr").strip()

        expression_match = re.search(
            r"(?P<expr>\d+(?:\.\d+)?(?:\s*(?:\*\*|[+\-*/%])\s*\d+(?:\.\d+)?)+)",
            user_input,
        )
        if expression_match:
            return expression_match.group("expr").strip()

        return None

    @staticmethod
    def _compose_answer(user_input: str, tool_results: list[ToolResult]) -> str:
        if not tool_results:
            return (
                "这个问题不需要调用工具。我会直接回答："
                "工具调用 Agent 的核心是让程序把可执行能力暴露给模型，"
                "由模型决定是否调用，再由程序执行并返回结果。"
            )

        result = tool_results[0]
        if not result.ok:
            return f"工具 {result.name} 执行失败：{result.error}"

        if result.name == "calculator":
            answer = f"计算结果：{result.output}"
            if "大于 100" in user_input and isinstance(result.output, int | float):
                answer += "，大于 100。" if result.output > 100 else "，不大于 100。"
            return answer

        if result.name == "search_text":
            output = result.output or {}
            if output.get("found"):
                return f"找到了关键词，共 {output['count']} 处命中。"
            return "没有找到该关键词。"

        if result.name == "get_current_time":
            output = result.output or {}
            return (
                f"当前日期是 {output.get('date')}，"
                f"当前时间是 {output.get('time')}，"
                f"时区是 {output.get('timezone')}。"
            )

        return f"工具 {result.name} 执行完成：{result.output}"
