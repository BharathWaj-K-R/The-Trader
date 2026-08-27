from datetime import datetime, timedelta, timezone

from app.models import Bar, StrategyParams
from app.strategy import MomentumStrategy, atr_pct, volume_ratio


def bars(values, volumes=None):
    volumes = volumes or [1.0] * len(values)
    start = datetime.now(timezone.utc)
    return [Bar(start + timedelta(minutes=i), v, v * 1.01, v * 0.99, v, volume) for i, (v, volume) in enumerate(zip(values, volumes))]


def test_warmup_returns_hold():
    strategy = MomentumStrategy(StrategyParams(fast_window=3, slow_window=5))
    assert strategy.signal(bars([1, 2, 3])).action == "HOLD"


def test_signal_is_valid_after_warmup():
    strategy = MomentumStrategy(StrategyParams(fast_window=3, slow_window=5))
    assert strategy.signal(bars([1, 1, 1, 1, 1, 2, 3, 4, 5, 6, 7])).action in {"BUY", "HOLD", "SELL"}


def test_context_indicators_are_defined_after_warmup():
    data = bars([100 + i for i in range(30)], [10 + i for i in range(30)])
    assert atr_pct(data, 14) is not None
    assert volume_ratio(data, 20) is not None


def test_trend_quality_filter_blocks_weak_trend():
    strategy = MomentumStrategy(StrategyParams(
        fast_window=3,
        slow_window=5,
        rsi_window=3,
        rsi_entry=50,
        use_trend_quality=True,
        min_trend_gap_pct=0.50,
    ))
    assert strategy.signal(bars([100, 100, 100, 100, 100, 101, 101, 101])).reason == "trend_quality_filter"


def test_volume_confirmation_blocks_low_volume_signal():
    data = bars([100, 100, 100, 100, 100, 102, 104, 106, 108], [10, 10, 10, 10, 10, 10, 10, 10, 1])
    strategy = MomentumStrategy(StrategyParams(
        fast_window=3,
        slow_window=5,
        rsi_window=3,
        rsi_entry=50,
        use_volume_confirmation=True,
        volume_window=5,
        min_volume_ratio=1.5,
    ))
    assert strategy.signal(data).reason == "volume_confirmation_filter"


def test_volatility_filter_blocks_extreme_move():
    data = bars([100, 100, 100, 100, 100, 150, 155, 160, 165, 170, 175, 180, 185, 190, 195, 200, 205])
    strategy = MomentumStrategy(StrategyParams(
        fast_window=3,
        slow_window=5,
        rsi_window=3,
        rsi_entry=50,
        use_volatility_filter=True,
        atr_window=5,
        min_atr_pct=0.0,
        max_atr_pct=0.01,
    ))
    assert strategy.signal(data).reason == "volatility_filter"
