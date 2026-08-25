from __future__ import annotations

from dataclasses import dataclass

from .config import settings


@dataclass(frozen=True)
class ExecutionPolicy:
    stop_loss_fraction: float = settings.stop_loss_fraction
    take_profit_fraction: float = settings.take_profit_fraction
    max_holding_bars: int = settings.max_holding_bars
    cooldown_bars: int = settings.cooldown_bars

    def protective_exit(self, entry_price: float, current_price: float) -> str | None:
        if entry_price <= 0 or current_price <= 0:
            return None
        change = current_price / entry_price - 1
        if self.stop_loss_fraction and change <= -self.stop_loss_fraction:
            return "protective_stop_loss"
        if self.take_profit_fraction and change >= self.take_profit_fraction:
            return "protective_take_profit"
        return None
