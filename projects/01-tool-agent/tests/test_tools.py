from tool_agent.tools import calculate, get_current_time, run_tool, search_text


def test_calculate_basic_expression():
    result = calculate("23 * 17")
    assert result.ok is True
    assert result.output == 391


def test_calculate_rejects_invalid_expression():
    result = calculate("abc + 1")
    assert result.ok is False
    assert result.error


def test_calculate_handles_zero_division():
    result = calculate("100 / 0")
    assert result.ok is False
    assert "0" in result.error


def test_search_text_found():
    result = search_text("LangGraph", "OpenAI Agents SDK 和 LangGraph 都可以做 Agent 编排。")
    assert result.ok is True
    assert result.output["found"] is True
    assert result.output["count"] == 1


def test_search_text_not_found():
    result = search_text("MCP", "RAG 负责知识检索。")
    assert result.ok is True
    assert result.output["found"] is False


def test_get_current_time():
    result = get_current_time("Asia/Shanghai")
    assert result.ok is True
    assert result.output["date"]
    assert result.output["time"]


def test_run_unknown_tool():
    result = run_tool("missing_tool", {})
    assert result.ok is False
    assert "未知工具" in result.error

