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

    def as_dict(self):
        return self.__dict__.copy()
