from __future__ import annotations

from typing import Any, Callable


ToolHandler = Callable[[dict[str, Any]], dict[str, Any]]


def tool_definitions() -> list[dict[str, Any]]:
    """Read-only tool contracts reserved for future multi-turn Grok tool loops."""
    return [
        {
            "type": "function",
            "name": "get_strategy",
            "description": "Return the currently active deterministic strategy parameters.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "type": "function",
            "name": "get_research_history",
            "description": "Return recent research reports and experiment outcomes.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "type": "function",
            "name": "get_risk_state",
            "description": "Return current risk and execution state. Never returns secrets.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "type": "function",
            "name": "get_recent_trades",
            "description": "Return recent persisted trades and their outcomes.",
            "parameters": {"type": "object", "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 50}}, "required": [], "additionalProperties": False},
        },
        {
            "type": "function",
            "name": "get_market_context",
            "description": "Return a compact recent OHLCV market context.",
            "parameters": {"type": "object", "properties": {"symbol": {"type": "string"}, "timeframe": {"type": "string"}, "bars": {"type": "integer", "minimum": 20, "maximum": 120}}, "required": ["symbol", "timeframe"], "additionalProperties": False},
        },
    ]


def dispatch(name: str, arguments: dict[str, Any], handlers: dict[str, ToolHandler]) -> dict[str, Any]:
    """Dispatch only registered read-only tools; unknown tools are rejected."""
    handler = handlers.get(name)
    if handler is None:
        raise ValueError(f"Unknown AI tool: {name}")
    return handler(arguments)
