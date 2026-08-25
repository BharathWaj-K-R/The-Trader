from dataclasses import dataclass
from datetime import date, datetime

from .config import settings


@dataclass
class RiskDecision:
    allowed: bool
    quantity: float
    reason: str


class RiskGuard:
    def __init__(self, initial_capital: float):
        self.high_watermark = initial_capital
        self.day_start_equity = initial_capital
        self.day_key = None

    def update(self, equity: float, timestamp=None):
        self.high_watermark = max(self.high_watermark, equity)
        if timestamp is not None:
            key = timestamp.date() if isinstance(timestamp, datetime) else timestamp
            if self.day_key is None:
                self.day_key = key
                self.day_start_equity = equity
            elif key != self.day_key:
                self.day_key = key
                self.day_start_equity = equity

    def check(self, equity: float, cash: float, price: float, requested_fraction: float, timestamp=None):
        self.update(equity, timestamp)
        drawdown = 1 - equity / self.high_watermark if self.high_watermark else 0.0
        daily_loss = 1 - equity / self.day_start_equity if self.day_start_equity else 0.0
        if drawdown >= settings.max_drawdown_fraction:
            return RiskDecision(False, 0.0, "max_drawdown_limit")
        if daily_loss >= settings.max_daily_loss_fraction:
            return RiskDecision(False, 0.0, "daily_loss_limit")
        fraction = min(max(requested_fraction, 0.0), settings.max_position_fraction)
        notional = min(cash, equity * fraction)
        quantity = notional / price if price > 0 else 0.0
        if quantity <= 0:
            return RiskDecision(False, 0.0, "insufficient_cash")
        return RiskDecision(True, quantity, "approved")
