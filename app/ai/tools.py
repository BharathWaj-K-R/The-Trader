from __future__ import annotations

import json
from typing import Any, Callable


ToolHandler = Callable[[dict[str, Any]], dict[str, Any]]


def tool_definitions() -> list[dict[str, Any]]:
    """Tool contracts exposed to Grok. All current tools are strictly read-only."""
    return [
        {
            "type": "function",
            "name": "get_strategy",
            "description": "Return active deterministic strategy parameters. Read-only.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "type": "function",
            "name": "get_research_history",
            "description": "Return recent research reports and experiment outcomes. Read-only.",
            "parameters": {"type": "object", "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 20}}, "required": [], "additionalProperties": False},
        },
        {
            "type": "function",
            "name": "get_risk_state",
            "description": "Return current risk and execution state without secrets. Read-only.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "type": "function",
            "name": "get_recent_trades",
            "description": "Return recent persisted trades and outcomes. Read-only.",
            "parameters": {"type": "object", "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 50}}, "required": [], "additionalProperties": False},
        },
        {
            "type": "function",
            "name": "get_market_context",
            "description": "Return validated recent OHLCV market context. Read-only.",
            "parameters": {"type": "object", "properties": {"symbol": {"type": "string"}, "timeframe": {"type": "string"}, "bars": {"type": "integer", "minimum": 20, "maximum": 120}}, "required": ["symbol", "timeframe"], "additionalProperties": False},
        },
    ]


def build_handlers(agent) -> dict[str, ToolHandler]:
    def market(args: dict[str, Any]) -> dict[str, Any]:
        symbol = str(args.get("symbol", "BTC/USDT")).strip().upper()
        timeframe = str(args.get("timeframe", "30m")).strip()
        bars = max(20, min(120, int(args.get("bars", 60))))
        rows = agent.market.fetch(symbol, timeframe, bars)
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "bars": [
                {"time": row.timestamp.isoformat(), "open": row.open, "high": row.high, "low": row.low, "close": row.close, "volume": row.volume}
                for row in rows
            ],
        }

    def strategy(_: dict[str, Any]) -> dict[str, Any]:
        return {"strategy": agent.params.as_dict()}

    def research(args: dict[str, Any]) -> dict[str, Any]:
        limit = max(1, min(20, int(args.get("limit", 10))))
        return {"reports": agent.store.recent("research_reports", limit), "experiments": agent.store.recent("experiments", limit)}

    def risk(_: dict[str, Any]) -> dict[str, Any]:
        return {"execution": agent.execution_status(), "paper": agent.paper_engine().snapshot()}

    def trades(args: dict[str, Any]) -> dict[str, Any]:
        limit = max(1, min(50, int(args.get("limit", 20))))
        return {"trades": agent.store.recent("trades", limit)}

    return {
        "get_strategy": strategy,
        "get_research_history": research,
        "get_risk_state": risk,
        "get_recent_trades": trades,
        "get_market_context": market,
    }


def dispatch(name: str, arguments: dict[str, Any], handlers: dict[str, ToolHandler]) -> dict[str, Any]:
    handler = handlers.get(name)
    if handler is None:
        raise ValueError(f"Unknown AI tool: {name}")
    return handler(arguments)
