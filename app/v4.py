from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from .config import settings
from .notifications import NotificationGate


UNIVERSE = ("SPY", "QQQ")
TIMEFRAME = "1h"


def product_manifest() -> dict[str, Any]:
    return {
        "product": "THE TRADER",
        "specification": "v4.0",
        "status": "paper_research_only",
        "universe": list(UNIVERSE),
        "timeframe": TIMEFRAME,
        "direction": "long_only",
        "primary_data": "yfinance",
        "secondary_validation": "stooq_daily_sanity_only",
        "paper_broker": "Alpaca Paper adapter supported; simulator remains available for deterministic local tests",
        "live_trading": False,
        "ai_execution_authority": False,
        "notification_authority": "generate_notifications_only",
        "risk_authority": "deterministic_absolute_veto",
        "human_authority": "final_manual_decision",
        "infrastructure_cost_target_inr": 0,
        "cpu_first": True,
    }


def validate_universe(symbol: str, timeframe: str) -> tuple[str, str]:
    symbol = symbol.strip().upper()
    timeframe = timeframe.strip()
    if symbol not in UNIVERSE:
        raise ValueError(f"v4 universe is limited to {', '.join(UNIVERSE)}")
    if timeframe != TIMEFRAME:
        raise ValueError("v4 initial timeframe is fixed to 1h")
    return symbol, timeframe


def notification_status(store, symbol: str) -> dict[str, Any]:
    gate = NotificationGate(store)
    metrics = gate.empirical_metrics(symbol)
    return {
        "policy": asdict(gate.policy),
        "metrics": metrics,
        "eligible": (
            metrics["sample_size"] >= gate.policy.min_rolling_sample
            and metrics["accuracy"] is not None
            and metrics["accuracy"] >= gate.policy.min_oos_accuracy
            and metrics["expectancy"] is not None
            and metrics["expectancy"] > gate.policy.min_rolling_expectancy
        ),
        "live_execution_enabled": False,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def safety_manifest() -> dict[str, Any]:
    return {
        "live_trading": "disabled_by_product_policy",
        "sandbox_trading": "disabled_by_product_policy",
        "derivatives": False,
        "leverage": False,
        "withdrawals": False,
        "autonomous_ai_execution": False,
        "risk_veto": True,
        "human_review": True,
    }
