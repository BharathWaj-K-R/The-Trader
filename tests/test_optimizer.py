from datetime import datetime, timezone
from app.models import Bar, StrategyParams
from app.optimizer import ScientificOptimizer


def make_bars(count=160):
    values = [100 + (i % 20) * 0.5 + i * 0.02 for i in range(count)]
    return [Bar(datetime.now(timezone.utc), v, v, v, v, 100) for v in values]


def test_optimizer_keeps_valid_strategy():
    params, result, history = ScientificOptimizer().improve(make_bars(), StrategyParams(), cycles=4)
    assert params.fast_window < params.slow_window
    assert len(history) >= 1
    assert "score" in result
