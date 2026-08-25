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
    }

    def __init__(self, store=None):
        self.store = store

    def candidate(self, baseline: StrategyParams):
        name = random.choice(list(self.MUTATIONS))
        delta = random.choice(self.MUTATIONS[name])
        candidate = copy.deepcopy(baseline)
        value = getattr(candidate, name) + delta
        if name == "fast_window":
            value = max(5, min(60, value))
        elif name == "slow_window":
            value = max(candidate.fast_window + 5, min(150, value))
        else:
            value = max(30, min(70, value))
        setattr(candidate, name, value)
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
