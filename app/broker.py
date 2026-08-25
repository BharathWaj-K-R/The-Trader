from datetime import datetime, timezone
from .config import settings
from .models import Trade

class PaperBroker:
    def __init__(self, cash: float):
        self.cash = cash
        self.asset = 0.0
        self.last_price = 0.0

    @property
    def equity(self):
        return self.cash + self.asset * self.last_price

    def mark(self, price: float):
        self.last_price = price

    def buy(self, price: float, quantity: float, reason: str):
        exec_price = price * (1 + settings.slippage_bps / 10000)
        fee = exec_price * quantity * settings.fee_bps / 10000
        total = exec_price * quantity + fee
        if total > self.cash:
            quantity = self.cash / (exec_price * (1 + settings.fee_bps / 10000))
            fee = exec_price * quantity * settings.fee_bps / 10000
        if quantity <= 0:
            return None
        self.cash -= exec_price * quantity + fee
        self.asset += quantity
        return Trade(datetime.now(timezone.utc), "BUY", exec_price, quantity, fee, 0.0, reason)

    def sell(self, price: float, quantity: float, reason: str):
        quantity = min(quantity, self.asset)
        if quantity <= 0:
            return None
        exec_price = price * (1 - settings.slippage_bps / 10000)
        fee = exec_price * quantity * settings.fee_bps / 10000
        proceeds = exec_price * quantity - fee
        self.cash += proceeds
        self.asset -= quantity
        return Trade(datetime.now(timezone.utc), "SELL", exec_price, quantity, fee, proceeds, reason)
