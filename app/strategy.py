from .models import Signal, StrategyParams


def sma(values, n):
    return sum(values[-n:]) / n if len(values) >= n else None


def rsi(values, n):
    if len(values) <= n:
        return None
    deltas = [b - a for a, b in zip(values[-n-1:-1], values[-n:])]
    gains = sum(max(d, 0.0) for d in deltas) / n
    losses = sum(max(-d, 0.0) for d in deltas) / n
    if losses == 0:
        return 100.0
    relative_strength = gains / losses
    return 100 - (100 / (1 + relative_strength))


def atr_pct(bars, n):
    if len(bars) <= n:
        return None
    true_ranges = []
    for index in range(len(bars) - n, len(bars)):
        current = bars[index]
        previous_close = bars[index - 1].close
        true_ranges.append(max(
            current.high - current.low,
            abs(current.high - previous_close),
            abs(current.low - previous_close),
        ))
    atr = sum(true_ranges) / n
    return atr / bars[-1].close if bars[-1].close else None


def volume_ratio(bars, n):
    if len(bars) < n + 1:
        return None
    baseline = sum(bar.volume for bar in bars[-n-1:-1]) / n
    return bars[-1].volume / baseline if baseline > 0 else None


class MomentumStrategy:
    def __init__(self, params: StrategyParams):
        if params.fast_window >= params.slow_window:
            raise ValueError("fast_window must be smaller than slow_window")
        if params.atr_window < 2 or params.volume_window < 2:
            raise ValueError("context windows must be at least 2")
        if params.min_atr_pct < 0 or params.max_atr_pct <= 0 or params.min_atr_pct > params.max_atr_pct:
            raise ValueError("invalid ATR filter bounds")
        if params.min_volume_ratio < 0:
            raise ValueError("min_volume_ratio cannot be negative")
        self.params = params

    def signal(self, bars):
        closes = [bar.close for bar in bars]
        fast = sma(closes, self.params.fast_window)
        slow = sma(closes, self.params.slow_window)
        strength = rsi(closes, self.params.rsi_window)
        if fast is None or slow is None or strength is None:
            return Signal("HOLD", 0.0, "warmup")

        trend_gap = abs(fast - slow) / slow if slow else 0.0
        volatility = atr_pct(bars, self.params.atr_window)
        volume = volume_ratio(bars, self.params.volume_window)

        if self.params.use_trend_quality and trend_gap < self.params.min_trend_gap_pct:
            return Signal("HOLD", 0.0, "trend_quality_filter")
        if self.params.use_volatility_filter:
            if volatility is None:
                return Signal("HOLD", 0.0, "volatility_warmup")
            if volatility < self.params.min_atr_pct or volatility > self.params.max_atr_pct:
                return Signal("HOLD", 0.0, "volatility_filter")
        if self.params.use_volume_confirmation:
            if volume is None:
                return Signal("HOLD", 0.0, "volume_warmup")
            if volume < self.params.min_volume_ratio:
                return Signal("HOLD", 0.0, "volume_confirmation_filter")

        quality_bonus = min(0.15, trend_gap * 10)
        if fast > slow and strength >= self.params.rsi_entry:
            confidence = min(1.0, max(0.0, (strength - 50) / 30) + quality_bonus)
            return Signal("BUY", confidence, "trend_up_rsi_confirmed")
        if fast < slow and strength <= self.params.rsi_exit:
            confidence = min(1.0, max(0.0, (50 - strength) / 30) + quality_bonus)
            return Signal("SELL", confidence, "trend_down_rsi_confirmed")
        return Signal("HOLD", 0.0, "no_edge")
