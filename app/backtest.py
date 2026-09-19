from .broker import PaperBroker
from .config import settings
from .goals import Goal
from .models import StrategyParams
from .policy import ExecutionPolicy
from .risk import RiskGuard
from .strategy import MomentumStrategy


def run_backtest(
    bars,
    params=None,
    initial_capital=None,
    policy=None,
    fee_bps=None,
    slippage_bps=None,
):
    if not bars:
        raise ValueError("bars cannot be empty")
    params = params or StrategyParams()
    capital = initial_capital if initial_capital is not None else settings.initial_capital
    policy = policy or ExecutionPolicy()
    strategy = MomentumStrategy(params)
    broker = PaperBroker(capital, fee_bps=fee_bps, slippage_bps=slippage_bps)
    risk = RiskGuard(capital)
    equity_curve, trades, history = [], [], []
    risk_violations = 0
    entry_bar_index = None
    cooldown_until = -1

    for index, bar in enumerate(bars):
        broker.mark(bar.close)
        history.append(bar)
        risk.update(broker.equity, bar.timestamp)
        equity_curve.append(broker.equity)

        if broker.asset > 0:
            protective_reason = policy.protective_exit(broker.average_entry_price, bar.close)
            max_hold_reason = (
                policy.max_holding_bars and entry_bar_index is not None
                and index - entry_bar_index >= policy.max_holding_bars
            )
            if protective_reason or max_hold_reason:
                reason = protective_reason or "max_holding_period"
                trade = broker.sell(bar.close, broker.asset, reason)
                if trade:
                    trades.append(trade)
                    entry_bar_index = None
                    cooldown_until = index + policy.cooldown_bars
                    broker.mark(bar.close)
                    equity_curve.append(broker.equity)
                    continue

        signal = strategy.signal(history)
        if signal.action == "BUY" and broker.asset <= 0 and index >= cooldown_until:
            decision = risk.check(
                broker.equity,
                broker.cash,
                bar.close,
                max(0.05, min(0.20, signal.confidence)),
                bar.timestamp,
            )
            if decision.allowed:
                trade = broker.buy(bar.close, decision.quantity, signal.reason)
                if trade:
                    trades.append(trade)
                    entry_bar_index = index
            else:
                risk_violations += 1
        elif signal.action == "SELL" and broker.asset > 0:
            trade = broker.sell(bar.close, broker.asset, signal.reason)
            if trade:
                trades.append(trade)
                entry_bar_index = None
                cooldown_until = index + policy.cooldown_bars

        broker.mark(bar.close)
        risk.update(broker.equity, bar.timestamp)
        equity_curve.append(broker.equity)

    benchmark_return = (bars[-1].close / bars[0].close - 1) if len(bars) >= 2 and bars[0].close else 0.0
    result = Goal().evaluate(equity_curve, trades, risk_violations, benchmark_return)
    return result, trades, equity_curve
