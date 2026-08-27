from dataclasses import dataclass
from datetime import datetime


@dataclass
class Bar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class Signal:
    action: str
    confidence: float
    reason: str


@dataclass
class Trade:
    timestamp: datetime
    side: str
    price: float
    quantity: float
    fee: float
    pnl: float
    reason: str


@dataclass
class StrategyParams:
    fast_window: int = 20
    slow_window: int = 50
    rsi_window: int = 14
    rsi_entry: float = 55.0
    rsi_exit: float = 45.0

    # Deterministic market-context knowledge layer.
    # Defaults remain permissive so legacy behavior is not silently altered.
    use_trend_quality: bool = False
    min_trend_gap_pct: float = 0.0
    use_volatility_filter: bool = False
    atr_window: int = 14
    min_atr_pct: float = 0.0
    max_atr_pct: float = 1.0
    use_volume_confirmation: bool = False
    volume_window: int = 20
    min_volume_ratio: float = 0.0

    def as_dict(self):
        return self.__dict__.copy()
