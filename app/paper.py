from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone

from .broker import PaperBroker
from .config import settings
from .models import StrategyParams
from .risk import RiskGuard
from .strategy import MomentumStrategy


class PaperEngine:
    """Restart-safe paper execution loop. It never submits real exchange orders."""

    def __init__(self, store, market, symbol=None, timeframe=None):
        self.store = store
        self.market = market
        self.symbol = symbol or settings.symbol
        self.timeframe = timeframe or settings.timeframe
        self.account_id = f"paper:{self.symbol}:{self.timeframe}"
        self.state = self._load()
        self.broker = self._broker_from_state()
        self.risk = RiskGuard(settings.initial_capital)
        self.risk.high_watermark = self.state["high_watermark"]
        self.risk.day_start_equity = self.state["day_start_equity"]
        self.params = StrategyParams(**self.state["strategy"])

    def _broker_from_state(self):
        broker = PaperBroker(self.state["cash"])
        broker.asset = self.state["asset"]
        broker.last_price = self.state["last_price"]
        broker.cost_basis = self.state["cost_basis"]
        broker.realized_pnl = self.state["realized_pnl"]
        return broker

    def _load(self):
        saved = self.store.get_paper_state(self.account_id)
        if saved:
            return saved
        return {
            "account_id": self.account_id,
            "cash": settings.initial_capital,
            "asset": 0.0,
            "last_price": 0.0,
            "cost_basis": 0.0,
            "realized_pnl": 0.0,
            "high_watermark": settings.initial_capital,
            "day_start_equity": settings.initial_capital,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "strategy": StrategyParams().as_dict(),
            "trading_halted": False,
        }

    def _persist(self):
        self.state.update({
            "cash": self.broker.cash,
            "asset": self.broker.asset,
            "last_price": self.broker.last_price,
            "cost_basis": self.broker.cost_basis,
            "realized_pnl": self.broker.realized_pnl,
            "high_watermark": self.risk.high_watermark,
            "day_start_equity": self.risk.day_start_equity,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "strategy": self.params.as_dict(),
        })
        self.store.save_paper_state(self.account_id, self.state)

    def tick(self, bars_limit=120):
        bars = self.market.fetch(self.symbol, self.timeframe, bars_limit)
        latest = bars[-1]
        self.broker.mark(latest.close)
        self.risk.update(self.broker.equity)
        if self.risk.high_watermark > 0:
            drawdown = 1 - self.broker.equity / self.risk.high_watermark
            if drawdown >= settings.max_drawdown_fraction:
                self.state["trading_halted"] = True

        if self.state.get("trading_halted"):
            self._persist()
            return {"action": "HALT", "reason": "risk_limit", **self.snapshot()}

        signal = MomentumStrategy(self.params).signal(bars)
        trade = None
        if signal.action == "BUY" and self.broker.asset <= 0:
            decision = self.risk.check(
                self.broker.equity,
                self.broker.cash,
                latest.close,
                max(0.05, min(0.20, signal.confidence)),
            )
            if decision.allowed:
                trade = self.broker.buy(latest.close, decision.quantity, signal.reason)
        elif signal.action == "SELL" and self.broker.asset > 0:
            trade = self.broker.sell(latest.close, self.broker.asset, signal.reason)

        self.broker.mark(latest.close)
        self.risk.update(self.broker.equity)
        self._persist()
        if trade:
            run_id = self.store.add_run("paper_tick", self.symbol, {"signal": asdict(signal)})
            self.store.add_trade(run_id, trade)
        return {"action": signal.action, "reason": signal.reason, "confidence": signal.confidence, **self.snapshot()}

    def reset(self):
        self.store.delete_paper_state(self.account_id)
        self.state = self._load()
        self.broker = self._broker_from_state()
        self.params = StrategyParams(**self.state["strategy"])
        return self.snapshot()

    def snapshot(self):
        return {
            "account_id": self.account_id,
            "cash": self.broker.cash,
            "asset": self.broker.asset,
            "last_price": self.broker.last_price,
            "equity": self.broker.equity,
            "average_entry_price": self.broker.average_entry_price,
            "realized_pnl": self.broker.realized_pnl,
            "drawdown_pct": (1 - self.broker.equity / self.risk.high_watermark) if self.risk.high_watermark else 0.0,
            "trading_halted": bool(self.state.get("trading_halted")),
            "strategy": self.params.as_dict(),
            "updated_at": self.state.get("updated_at"),
        }
