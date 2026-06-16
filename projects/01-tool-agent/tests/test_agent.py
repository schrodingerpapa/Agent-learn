from tool_agent.agent import RuleBasedToolAgent


def test_agent_calls_calculator():
    response = RuleBasedToolAgent().run("帮我计算 23 * 17")
    assert response.tool_calls[0].name == "calculator"
    assert "391" in response.final_answer


def test_agent_calls_search_text():
    response = RuleBasedToolAgent().run(
        "在这段文本里搜索 LangGraph：OpenAI Agents SDK 和 LangGraph 都可以做 Agent 编排。"
    )
    assert response.tool_calls[0].name == "search_text"
    assert "找到了" in response.final_answer


def test_agent_calls_time_tool():
    response = RuleBasedToolAgent().run("现在几点？")
    assert response.tool_calls[0].name == "get_current_time"
    assert "当前时间" in response.final_answer


def test_agent_does_not_call_tool_for_concept_question():
    response = RuleBasedToolAgent().run("请解释一下什么是 Agent loop")
    assert response.tool_calls == []
    assert "不需要调用工具" in response.final_answer


def test_agent_trace_records_full_flow():
    response = RuleBasedToolAgent().run("帮我计算 23 * 17")
    stages = [step.stage for step in response.trace]
    assert stages == [
        "input.received",
        "planning.completed",
        "tool.started",
        "tool.completed",
        "answer.completed",
    ]
    assert response.trace[1].data["tool_calls"][0]["name"] == "calculator"
    assert response.trace[3].data["output"] == 391
