from datetime import datetime, timezone

from .config import settings
from .models import Trade


class PaperBroker:
    def __init__(self, cash: float, fee_bps: float | None = None, slippage_bps: float | None = None):
        self.cash = cash
        self.asset = 0.0
        self.last_price = 0.0
        self.cost_basis = 0.0
        self.realized_pnl = 0.0
        self.fee_bps = settings.fee_bps if fee_bps is None else fee_bps
        self.slippage_bps = settings.slippage_bps if slippage_bps is None else slippage_bps

    @property
    def equity(self):
        return self.cash + self.asset * self.last_price

    @property
    def average_entry_price(self):
        return self.cost_basis / self.asset if self.asset else 0.0

    def mark(self, price: float):
        if price <= 0:
            raise ValueError("price must be positive")
        self.last_price = price

    def buy(self, price: float, quantity: float, reason: str):
        if price <= 0 or quantity <= 0:
            return None
        exec_price = price * (1 + self.slippage_bps / 10000)
        fee = exec_price * quantity * self.fee_bps / 10000
        total = exec_price * quantity + fee
        if total > self.cash:
            quantity = self.cash / (exec_price * (1 + self.fee_bps / 10000))
            fee = exec_price * quantity * self.fee_bps / 10000
        if quantity <= 0:
            return None
        total_cost = exec_price * quantity + fee
        self.cash -= total_cost
        self.asset += quantity
        self.cost_basis += total_cost
        return Trade(datetime.now(timezone.utc), "BUY", exec_price, quantity, fee, 0.0, reason)

    def sell(self, price: float, quantity: float, reason: str):
        if price <= 0:
            raise ValueError("price must be positive")
        quantity = min(quantity, self.asset)
        if quantity <= 0:
            return None
        exec_price = price * (1 - self.slippage_bps / 10000)
        fee = exec_price * quantity * self.fee_bps / 10000
        proceeds = exec_price * quantity - fee
        average_cost = self.average_entry_price
        cost_removed = average_cost * quantity
        pnl = proceeds - cost_removed
        self.cash += proceeds
        self.asset -= quantity
        self.cost_basis -= cost_removed
        if self.asset < 1e-12:
            self.asset = 0.0
            self.cost_basis = 0.0
        self.realized_pnl += pnl
        return Trade(datetime.now(timezone.utc), "SELL", exec_price, quantity, fee, pnl, reason)
