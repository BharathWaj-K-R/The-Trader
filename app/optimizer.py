import copy
import random

from .backtest import run_backtest
from .models import StrategyParams


class ScientificOptimizer:
    MUTATIONS = {
        "fast_window": (-2, 2),
        "slow_window": (-5, 5),
        "rsi_entry": (-2, 2),
        "rsi_exit": (-2, 2),
        "min_trend_gap_pct": (-0.001, 0.001),
        "min_atr_pct": (-0.001, 0.001),
        "max_atr_pct": (-0.01, 0.01),
        "min_volume_ratio": (-0.05, 0.05),
    }

    def __init__(self, store=None, seed=None):
        self.store = store
        self.random = random.Random(seed)

    def candidate(self, baseline: StrategyParams):
        name = self.random.choice(list(self.MUTATIONS))
        delta = self.random.choice(self.MUTATIONS[name])
        candidate = copy.deepcopy(baseline)
        value = getattr(candidate, name) + delta
        if name == "fast_window":
            value = max(5, min(60, int(value)))
        elif name == "slow_window":
            value = max(candidate.fast_window + 5, min(150, int(value)))
        elif name == "min_trend_gap_pct":
            value = max(0.0, min(0.10, value))
        elif name == "min_atr_pct":
            value = max(0.0, min(1.0, value))
        elif name == "max_atr_pct":
            value = max(0.001, min(1.0, value))
        elif name == "min_volume_ratio":
            value = max(0.0, min(5.0, value))
        else:
            value = max(30, min(70, value))
        setattr(candidate, name, value)
        if candidate.min_atr_pct > candidate.max_atr_pct:
            candidate.max_atr_pct = candidate.min_atr_pct
        return name, candidate

    def improve(self, bars, baseline: StrategyParams, cycles=5):
        current = copy.deepcopy(baseline)
        current_result, _, _ = run_backtest(bars, current)
        history = [{
            "params": current.as_dict(),
            "score": current_result["score"],
            "accepted": True,
            "reason": "initial_baseline",
        }]

        for _ in range(cycles):
            changed, candidate = self.candidate(current)
            if candidate.fast_window >= candidate.slow_window:
                continue
            result, _, _ = run_backtest(bars, candidate)
            accepted = result["score"] > current_result["score"]
            reason = f"changed_only={changed}"
            if self.store:
                self.store.add_experiment(
                    current.as_dict(), candidate.as_dict(),
                    current_result["score"], result["score"], accepted, reason,
                )
            history.append({
                "params": candidate.as_dict(),
                "score": result["score"],
                "accepted": accepted,
                "reason": reason,
            })
            if accepted:
                current, current_result = candidate, result

        if self.store:
            self.store.activate_strategy(current.as_dict(), current_result["score"])
        return current, current_result, history
