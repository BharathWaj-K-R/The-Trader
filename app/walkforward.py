from __future__ import annotations

import copy

from .backtest import run_backtest
from .models import StrategyParams
from .optimizer import ScientificOptimizer


def run_walk_forward(bars, baseline: StrategyParams, folds: int = 4, cycles: int = 6):
    if len(bars) < 160:
        raise ValueError("walk-forward validation needs at least 160 bars")
    if folds < 2 or folds > 8:
        raise ValueError("folds must be between 2 and 8")

    fold_size = len(bars) // folds
    results = []
    selected = copy.deepcopy(baseline)

    for fold in range(1, folds):
        test_start = fold * fold_size
        test_end = len(bars) if fold == folds - 1 else (fold + 1) * fold_size
        train = bars[:test_start]
        test = bars[test_start:test_end]
        if len(test) < 20:
            continue

        optimizer = ScientificOptimizer(store=None, seed=fold)
        selected, train_goal, _ = optimizer.improve(train, selected, cycles=cycles)
        test_goal, test_trades, _ = run_backtest(test, selected)
        results.append({
            "fold": fold,
            "train_bars": len(train),
            "test_bars": len(test),
            "strategy": selected.as_dict(),
            "train_score": train_goal["score"],
            "test_score": test_goal["score"],
            "test_return_pct": test_goal["return_pct"],
            "test_max_drawdown_pct": test_goal["max_drawdown_pct"],
            "test_trades": len(test_trades),
            "test_success": test_goal["success"],
        })

    if not results:
        raise RuntimeError("no walk-forward folds could be evaluated")

    avg_score = sum(r["test_score"] for r in results) / len(results)
    avg_return = sum(r["test_return_pct"] for r in results) / len(results)
    worst_drawdown = max(r["test_max_drawdown_pct"] for r in results)
    positive_folds = sum(1 for r in results if r["test_return_pct"] > 0)
    robust = positive_folds >= max(1, len(results) // 2) and worst_drawdown < 0.20

    return {
        "folds_evaluated": len(results),
        "average_test_score": avg_score,
        "average_test_return_pct": avg_return,
        "worst_test_drawdown_pct": worst_drawdown,
        "positive_folds": positive_folds,
        "robust": robust,
        "final_candidate": selected.as_dict(),
        "fold_results": results,
    }
