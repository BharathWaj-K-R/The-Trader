from dataclasses import dataclass
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

    def update(self, equity: float):
        self.high_watermark = max(self.high_watermark, equity)

    def check(self, equity: float, cash: float, price: float, requested_fraction: float):
        self.update(equity)
        drawdown = 1 - equity / self.high_watermark
        daily_loss = 1 - equity / self.day_start_equity
        if drawdown >= settings.max_drawdown_fraction:
            return RiskDecision(False, 0.0, "max_drawdown_limit")
        if daily_loss >= settings.max_daily_loss_fraction:
            return RiskDecision(False, 0.0, "daily_loss_limit")
        fraction = min(requested_fraction, settings.max_position_fraction)
        notional = min(cash, equity * fraction)
        quantity = notional / price
        if quantity <= 0:
            return RiskDecision(False, 0.0, "insufficient_cash")
        return RiskDecision(True, quantity, "approved")
