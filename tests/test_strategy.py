from datetime import datetime, timezone
from app.models import Bar, StrategyParams
from app.strategy import MomentumStrategy


def bars(values):
    return [Bar(datetime.now(timezone.utc), v, v, v, v, 1.0) for v in values]


def test_warmup_returns_hold():
    strategy = MomentumStrategy(StrategyParams(fast_window=3, slow_window=5))
    assert strategy.signal(bars([1, 2, 3])).action == "HOLD"


def test_signal_is_valid_after_warmup():
    strategy = MomentumStrategy(StrategyParams(fast_window=3, slow_window=5))
    assert strategy.signal(bars([1, 1, 1, 1, 1, 2, 3, 4, 5, 6, 7])).action in {"BUY", "HOLD", "SELL"}
