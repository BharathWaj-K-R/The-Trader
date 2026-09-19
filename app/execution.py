from __future__ import annotations

import hmac
import math
from datetime import datetime, timezone

import ccxt

from .config import settings


class ExecutionError(RuntimeError):
    pass


class ExchangeGateway:
    """CCXT-backed spot gateway with explicit sandbox/live separation."""

    def __init__(self):
        if settings.exchange_id != "binance":
            raise ExecutionError("Only Binance is wired in this production adapter")
        config = {
            "apiKey": settings.exchange_api_key,
            "secret": settings.exchange_secret,
            "enableRateLimit": True,
        }
        if settings.exchange_password:
            config["password"] = settings.exchange_password
        try:
            exchange_cls = getattr(ccxt, settings.exchange_id)
        except AttributeError as exc:
            raise ExecutionError(f"Unsupported exchange: {settings.exchange_id}") from exc
        self.exchange = exchange_cls(config)
        if settings.execution_mode == "sandbox":
            self.exchange.set_sandbox_mode(True)

    def load(self):
        self.exchange.load_markets()
        return self.exchange

    def market(self, symbol):
        self.load()
        if symbol not in self.exchange.markets:
            raise ExecutionError(f"Symbol is not available: {symbol}")
        market = self.exchange.market(symbol)
        if not market.get("spot", False):
            raise ExecutionError("Only spot markets are supported by this execution gateway")
        return market

    def balance(self):
        self.load()
        return self.exchange.fetch_balance()

    def ticker(self, symbol):
        self.market(symbol)
        return self.exchange.fetch_ticker(symbol)

    def create_order(self, symbol, order_type, side, amount, price=None):
        self.market(symbol)
        if order_type not in {"market", "limit"}:
            raise ExecutionError("Only market and limit spot orders are supported")
        if side not in {"buy", "sell"}:
            raise ExecutionError("Invalid order side")
        return self.exchange.create_order(symbol, order_type, side, amount, price)

    def fetch_order(self, order_id, symbol):
        self.market(symbol)
        return self.exchange.fetch_order(order_id, symbol)

    def fetch_open_orders(self, symbol=None):
        if symbol:
            self.market(symbol)
        else:
            self.load()
        return self.exchange.fetch_open_orders(symbol)

    def cancel_order(self, order_id, symbol):
        self.market(symbol)
        return self.exchange.cancel_order(order_id, symbol)


class LiveExecutionEngine:
    """Spot execution with explicit arming, limits, risk halts and reconciliation."""

    def __init__(self, store):
        self.store = store
        self.account_id = f"{settings.execution_mode}:{settings.exchange_id}"
        self.gateway = ExchangeGateway() if settings.execution_mode in {"sandbox", "live"} else None
        control = self.store.get_execution_control(self.account_id)
        self.armed = control["armed"]
        self.kill_switch = control["kill_switch"] or settings.kill_switch

    @property
    def enabled(self):
        return settings.execution_mode in {"sandbox", "live"}

    def _control_metadata(self):
        return self.store.get_execution_control(self.account_id).get("metadata", {})

    def _save_control(self, metadata=None):
        current = self._control_metadata()
        if metadata:
            current.update(metadata)
        self.store.save_execution_control(self.account_id, self.armed, self.kill_switch, current)

    def _mark_risk_state(self, equity, now=None):
        now = now or datetime.now(timezone.utc)
        meta = self._control_metadata()
        day_key = now.date().isoformat()
        if meta.get("day_key") != day_key:
            meta["day_key"] = day_key
            meta["day_start_equity"] = float(equity)
        high = max(float(meta.get("high_watermark", equity)), float(equity))
        meta["high_watermark"] = high
        self._save_control(meta)
        daily_loss = 1 - float(equity) / float(meta["day_start_equity"]) if meta.get("day_start_equity") else 0.0
        drawdown = 1 - float(equity) / high if high else 0.0
        return daily_loss, drawdown

    def _quote_equity(self, symbol, balance=None, price=None):
        base, quote = symbol.split("/")
        balance = balance or self.gateway.balance()
        ticker_price = price
        if ticker_price is None:
            ticker_price = self.gateway.ticker(symbol).get("last")
        if not ticker_price or ticker_price <= 0:
            raise ExecutionError("Unable to value live portfolio")
        total = balance.get("total", {}) or {}
        quote_total = float(total.get(quote, 0.0) or 0.0)
        base_total = float(total.get(base, 0.0) or 0.0)
        return quote_total + base_total * float(ticker_price), balance, float(ticker_price)

    def _risk_check(self, symbol):
        equity, balance, price = self._quote_equity(symbol)
        daily_loss, drawdown = self._mark_risk_state(equity)
        if daily_loss >= settings.max_daily_loss_fraction:
            self.kill_switch = True
            self.armed = False
            self._save_control({"last_halt_reason": "max_daily_loss"})
            raise ExecutionError("Daily live-loss limit reached; execution halted")
        if drawdown >= settings.max_drawdown_fraction:
            self.kill_switch = True
            self.armed = False
            self._save_control({"last_halt_reason": "max_drawdown"})
            raise ExecutionError("Maximum live drawdown reached; execution halted")
        return equity, balance, price

    def preflight(self, symbol=None):
        if not self.enabled:
            return {"ready": False, "reason": "execution_mode_is_paper"}
        if self.kill_switch:
            return {"ready": False, "reason": "kill_switch_active"}
        if settings.execution_mode == "live" and not settings.live_trading_enabled:
            return {"ready": False, "reason": "live_trading_disabled"}
        try:
            self.gateway.load()
            ticker = self.gateway.ticker(symbol) if symbol else None
            balance = self.gateway.balance()
            risk = None
            if symbol and ticker:
                equity, _, _ = self._quote_equity(symbol, balance, ticker.get("last") or ticker.get("close"))
                daily_loss, drawdown = self._mark_risk_state(equity)
                risk = {"equity_quote": equity, "daily_loss": daily_loss, "drawdown": drawdown}
                if daily_loss >= settings.max_daily_loss_fraction or drawdown >= settings.max_drawdown_fraction:
                    return {"ready": False, "reason": "risk_limit_reached", "risk": risk}
            return {
                "ready": True,
                "mode": settings.execution_mode,
                "exchange": settings.exchange_id,
                "symbol": symbol,
                "ticker": ticker,
                "balance": balance,
                "risk": risk,
                "armed": self.armed,
                "kill_switch": self.kill_switch,
            }
        except Exception as exc:
            return {"ready": False, "reason": str(exc)}

    def arm(self, token: str):
        if not self.enabled:
            raise ExecutionError("Cannot arm while execution mode is paper")
        if settings.execution_mode == "live":
            expected = settings.live_confirmation_token or ""
            if not hmac.compare_digest(token or "", expected):
                raise ExecutionError("Invalid live confirmation token")
        self.armed = True
        self.kill_switch = False
        self._save_control()
        return self.status()

    def disarm(self):
        self.armed = False
        self._save_control()
        return self.status()

    def activate_kill_switch(self):
        self.kill_switch = True
        self.armed = False
        self._save_control({"last_halt_reason": "operator_kill_switch"})
        return self.status()

    def reset_kill_switch(self, token: str):
        if settings.execution_mode == "live":
            expected = settings.live_confirmation_token or ""
            if not hmac.compare_digest(token or "", expected):
                raise ExecutionError("Invalid live confirmation token")
        self.kill_switch = False
        self._save_control()
        return self.status()

    def status(self):
        control = self.store.get_execution_control(self.account_id)
        return {
            "enabled": self.enabled,
            "mode": settings.execution_mode,
            "exchange": settings.exchange_id,
            "armed": bool(control["armed"]),
            "kill_switch": bool(control["kill_switch"]),
            "orders_today": self.store.count_execution_orders_today(self.account_id),
            "max_orders_per_day": settings.max_live_orders_per_day,
            "max_order_notional": settings.max_live_order_notional,
            "risk_state": control.get("metadata", {}),
            "recent_orders": self.store.recent_execution_orders(self.account_id, 10),
        }

    def _require_armed(self, symbol):
        if not self.enabled:
            raise ExecutionError("Execution is configured for paper mode")
        if self.kill_switch:
            raise ExecutionError("Kill switch is active")
        if not self.armed:
            raise ExecutionError("Execution engine is disarmed")
        if self.store.count_execution_orders_today(self.account_id) >= settings.max_live_orders_per_day:
            raise ExecutionError("Daily live order limit reached")
        self._risk_check(symbol)

    def _notional(self, symbol, amount, price=None):
        ref_price = price
        if ref_price is None:
            ticker = self.gateway.ticker(symbol)
            ref_price = ticker.get("last") or ticker.get("close") or ticker.get("ask") or ticker.get("bid")
        if not ref_price or ref_price <= 0:
            raise ExecutionError("No valid reference price available")
        return float(amount) * float(ref_price)

    def place_order(self, symbol, order_type, side, amount, price=None, reason="manual"):
        self._require_armed(symbol)
        if amount <= 0 or not math.isfinite(amount):
            raise ExecutionError("amount must be a positive finite number")
        notional = self._notional(symbol, amount, price)
        if notional > settings.max_live_order_notional:
            raise ExecutionError(f"Order notional {notional:.4f} exceeds limit {settings.max_live_order_notional:.4f}")
        market = self.gateway.market(symbol)
        limits = market.get("limits", {})
        min_amount = (limits.get("amount") or {}).get("min")
        if min_amount and amount < min_amount:
            raise ExecutionError(f"amount is below exchange minimum {min_amount}")
        amount = float(self.gateway.exchange.amount_to_precision(symbol, amount))
        if order_type == "limit":
            if price is None or price <= 0:
                raise ExecutionError("limit orders require a positive price")
            price = float(self.gateway.exchange.price_to_precision(symbol, price))
        order = self.gateway.create_order(symbol, order_type, side, amount, price)
        order["local_reason"] = reason
        self.store.add_execution_order(self.account_id, order)
        return order

    def cancel_order(self, order_id, symbol):
        self._require_armed(symbol)
        order = self.gateway.cancel_order(order_id, symbol)
        self.store.update_execution_order(order_id, order)
        return order

    def reconcile(self, symbol=None):
        if not self.enabled:
            return {"reconciled": False, "reason": "execution_mode_is_paper"}
        self.gateway.load()
        balance = self.gateway.balance()
        open_orders = self.gateway.fetch_open_orders(symbol) if symbol else self.gateway.fetch_open_orders()
        local = self.store.recent_execution_orders(self.account_id, 200)
        updates = []
        for row in local:
            exchange_id = row.get("exchange_order_id")
            if not exchange_id or row.get("status") in {"closed", "canceled", "rejected", "expired"}:
                continue
            try:
                fresh = self.gateway.fetch_order(exchange_id, row["symbol"])
                self.store.update_execution_order(exchange_id, fresh)
                updates.append(fresh)
            except Exception:
                continue
        snapshot = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": settings.execution_mode,
            "exchange": settings.exchange_id,
            "balance": balance,
            "open_orders": open_orders,
            "updated_orders": updates,
        }
        self.store.add_execution_snapshot(self.account_id, snapshot)
        if symbol:
            try:
                equity, _, _ = self._quote_equity(symbol, balance)
                self._mark_risk_state(equity)
            except Exception:
                pass
        return {"reconciled": True, "open_orders": open_orders, "updated_orders": updates, "balance": balance}

    def signal_tick(self, symbol, timeframe, strategy):
        self._require_armed(symbol)
        from .data import MarketData

        bars = MarketData(settings.data_source).fetch(symbol, timeframe, 120)
        signal = strategy.signal(bars)
        if signal.action == "HOLD":
            return {"action": "HOLD", "reason": signal.reason}
        equity, balance, last = self._quote_equity(symbol)
        base, quote = symbol.split("/")
        free = balance.get("free", {}) or {}
        if signal.action == "BUY":
            quote_free = float(free.get(quote, 0.0) or 0.0)
            notional = min(quote_free * settings.max_position_fraction, settings.max_live_order_notional, equity * settings.max_position_fraction)
            if notional <= 0:
                return {"action": "HOLD", "reason": "insufficient_quote_balance"}
            amount = notional / last
            order = self.place_order(symbol, "market", "buy", amount, reason=signal.reason)
        else:
            base_free = float(free.get(base, 0.0) or 0.0)
            amount = min(base_free, settings.max_live_order_notional / last)
            if amount <= 0:
                return {"action": "HOLD", "reason": "no_base_balance"}
            order = self.place_order(symbol, "market", "sell", amount, reason=signal.reason)
        return {"signal": signal.__dict__, "order": order, "equity_quote": equity}
