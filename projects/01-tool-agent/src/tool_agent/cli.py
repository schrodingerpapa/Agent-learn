from __future__ import annotations

import argparse
import json

from .agent import RuleBasedToolAgent
from .tools import tool_schemas


def _print_response(response, as_json: bool = False, show_trace: bool = False) -> None:
    if as_json:
        print(json.dumps(response.to_dict(), ensure_ascii=False, indent=2))
        return

    if show_trace:
        _print_trace(response)
        return

    print("\n用户输入：")
    print(response.user_input)

    print("\n工具调用：")
    if not response.tool_calls:
        print("- 无")
    for call, result in zip(response.tool_calls, response.tool_results, strict=True):
        print(f"- {call.name}({json.dumps(call.arguments, ensure_ascii=False)})")
        if result.ok:
            print(f"  输出：{json.dumps(result.output, ensure_ascii=False)}")
        else:
            print(f"  错误：{result.error}")

    print("\n最终回答：")
    print(response.final_answer)


def _print_trace(response) -> None:
    print("\n=== Agent Trace ===")
    for index, step in enumerate(response.trace, start=1):
        print(f"\n[{index}] {step.stage}")
        print(step.message)
        print(json.dumps(step.data, ensure_ascii=False, indent=2))

    print("\n=== Final Answer ===")
    print(response.final_answer)


def _interactive_loop(agent: RuleBasedToolAgent, as_json: bool, show_trace: bool) -> None:
    print("Tool Agent CLI。输入 exit 或 quit 退出。")
    while True:
        user_input = input("\n> ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break
        if not user_input:
            continue
        _print_response(agent.run(user_input), as_json=as_json, show_trace=show_trace)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a minimal tool-calling agent from the command line."
    )
    parser.add_argument(
        "prompt",
        nargs="*",
        help="用户输入。留空则进入交互模式。",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="用 JSON 输出完整运行结果。",
    )
    parser.add_argument(
        "--trace",
        "--debug",
        action="store_true",
        dest="trace",
        help="打印 Agent loop 的逐步调试流程。",
    )
    parser.add_argument(
        "--show-tools",
        action="store_true",
        help="打印当前可用工具的 schema。",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.show_tools:
        print(json.dumps(tool_schemas(), ensure_ascii=False, indent=2))
        return

    agent = RuleBasedToolAgent()
    prompt = " ".join(args.prompt).strip()
    if prompt:
        _print_response(agent.run(prompt), as_json=args.json, show_trace=args.trace)
        return

    _interactive_loop(agent, as_json=args.json, show_trace=args.trace)


if __name__ == "__main__":
    main()
