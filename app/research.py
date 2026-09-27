from __future__ import annotations

from datetime import datetime, timezone

from .analytics import summarize_equity
from .backtest import run_backtest
from .config import settings
from .models import StrategyParams
from .optimizer import ScientificOptimizer
from .stress import run_cost_sensitivity
from .walkforward import run_walk_forward


def run_full_research(
    bars,
    baseline: StrategyParams,
    symbol: str | None = None,
    timeframe: str | None = None,
    cycles: int = 10,
    folds: int = 4,
):
    """Run the deterministic research pipeline without granting execution authority."""
    if len(bars) < 200:
        raise ValueError("full research needs at least 200 bars")

    symbol = symbol or settings.symbol
    timeframe = timeframe or settings.timeframe
    started_at = datetime.now(timezone.utc).isoformat()
    baseline = StrategyParams(**baseline.as_dict())

    baseline_goal, baseline_trades, baseline_equity = run_backtest(
        bars, baseline, settings.initial_capital
    )
    baseline_analytics = summarize_equity(
        baseline_equity, baseline_trades, [bar.close for bar in bars]
    )

    candidate, candidate_goal, experiments = ScientificOptimizer(seed=42).improve(
        bars, baseline, cycles
    )
    candidate_goal, candidate_trades, candidate_equity = run_backtest(
        bars, candidate, settings.initial_capital
    )
    candidate_analytics = summarize_equity(
        candidate_equity, candidate_trades, [bar.close for bar in bars]
    )

    walk_forward = run_walk_forward(
        bars, candidate, folds=folds, cycles=max(3, min(8, cycles // 2))
    )
    cost_stress = run_cost_sensitivity(bars, candidate)

    promoted = (
        walk_forward["robust"]
        and cost_stress["robust_scenarios"] >= max(1, cost_stress["scenarios"] // 2)
        and candidate_goal["score"] > baseline_goal["score"]
        and candidate_goal["excess_return_pct"] >= baseline_goal["excess_return_pct"]
    )

    return {
        "specification": "v4.0",
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "symbol": symbol,
        "timeframe": timeframe,
        "bars": len(bars),
        "baseline": {"params": baseline.as_dict(), "goal": baseline_goal, "analytics": baseline_analytics},
        "candidate": {"params": candidate.as_dict(), "goal": candidate_goal, "analytics": candidate_analytics},
        "experiments": experiments,
        "walk_forward": walk_forward,
        "cost_stress": cost_stress,
        "promotion": {
            "promoted": promoted,
            "reason": "all implemented deterministic gates passed" if promoted else "candidate failed at least one deterministic gate",
        },
        "final_test_protected": True,
        "live_trading_authority": False,
    }
