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

class MomentumStrategy:
    def __init__(self, params: StrategyParams):
        if params.fast_window >= params.slow_window:
            raise ValueError("fast_window must be smaller than slow_window")
        self.params = params

    def signal(self, bars):
        closes = [bar.close for bar in bars]
        fast = sma(closes, self.params.fast_window)
        slow = sma(closes, self.params.slow_window)
        strength = rsi(closes, self.params.rsi_window)
        if fast is None or slow is None or strength is None:
            return Signal("HOLD", 0.0, "warmup")
        if fast > slow and strength >= self.params.rsi_entry:
            return Signal("BUY", min(1.0, max(0.0, (strength - 50) / 30)), "trend_up_rsi_confirmed")
        if fast < slow and strength <= self.params.rsi_exit:
            return Signal("SELL", min(1.0, max(0.0, (50 - strength) / 30)), "trend_down_rsi_confirmed")
        return Signal("HOLD", 0.0, "no_edge")
