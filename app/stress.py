from __future__ import annotations

from .backtest import run_backtest
from .models import StrategyParams


def run_cost_sensitivity(
    bars,
    params: StrategyParams,
    fee_scenarios=(5.0, 10.0, 20.0),
    slippage_scenarios=(0.0, 5.0, 10.0, 20.0),
):
    results = []
    for fee in fee_scenarios:
        for slippage in slippage_scenarios:
            goal, trades, _ = run_backtest(
                bars,
                params,
                fee_bps=fee,
                slippage_bps=slippage,
            )
            results.append({
                "fee_bps": fee,
                "slippage_bps": slippage,
                "score": goal["score"],
                "return_pct": goal["return_pct"],
                "excess_return_pct": goal["excess_return_pct"],
                "max_drawdown_pct": goal["max_drawdown_pct"],
                "trades": len(trades),
                "success": goal["success"],
            })
    worst = min(results, key=lambda item: item["score"])
    return {
        "scenarios": len(results),
        "worst_case": worst,
        "profitable_scenarios": sum(1 for item in results if item["return_pct"] > 0),
        "robust_scenarios": sum(1 for item in results if item["success"]),
        "results": results,
    }
