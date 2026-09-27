from unittest.mock import patch

from app.ai.client import LocalAIClient
from app.ai.tools import tool_definitions


def test_web_tools_use_ollama_function_schema():
    tools = tool_definitions(internet=True)
    names = {item["function"]["name"] for item in tools}
    assert {"web_search", "web_fetch"} <= names
    assert all(item["type"] == "function" and "function" in item for item in tools)


def test_web_tools_are_absent_by_default():
    names = {item["function"]["name"] for item in tool_definitions()}
    assert "web_search" not in names
    assert "web_fetch" not in names


def test_web_tool_trace_records_call():
    client = LocalAIClient(model="qwen2.5:7b")
    responses = [
        {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"function": {"name": "web_search", "arguments": {"query": "SPY"}}}],
            },
            "prompt_eval_count": 1,
            "eval_count": 1,
        },
        {
            "message": {"role": "assistant", "content": "I used the web result."},
            "prompt_eval_count": 1,
            "eval_count": 1,
        },
        {
            "message": {"role": "assistant", "content": '{"verdict":"supported"}'},
            "prompt_eval_count": 1,
            "eval_count": 1,
        },
    ]
    with patch.object(client, "_request", side_effect=responses):
        value, usage = client.structured_with_tools(
            system="test",
            user="research",
            schema={"type": "object", "properties": {"verdict": {"type": "string"}}, "required": ["verdict"]},
            tools=tool_definitions(internet=True),
            handlers={"web_search": lambda args: {"ok": True, "provider": "test", "results": [{"url": "https://example.com"}]}},
        )
    assert value["verdict"] == "supported"
    assert usage["tool_trace"][0]["tool"] == "web_search"
    assert usage["tool_trace"][0]["status"] == "completed"
