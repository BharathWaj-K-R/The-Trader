from .broker import PaperBroker
from .goals import Goal
from .models import StrategyParams
from .risk import RiskGuard
from .strategy import MomentumStrategy


def run_backtest(bars, params=None, initial_capital=10000.0):
    if not bars:
        raise ValueError("bars cannot be empty")
    params = params or StrategyParams()
    strategy = MomentumStrategy(params)
    broker = PaperBroker(initial_capital)
    risk = RiskGuard(initial_capital)
    equity_curve, trades, history = [], [], []
    risk_violations = 0

    for bar in bars:
        broker.mark(bar.close)
        equity_curve.append(broker.equity)
        history.append(bar)
        signal = strategy.signal(history)

        if signal.action == "BUY" and broker.asset <= 0:
            decision = risk.check(
                broker.equity,
                broker.cash,
                bar.close,
                max(0.05, min(0.20, signal.confidence)),
            )
            if decision.allowed:
                trade = broker.buy(bar.close, decision.quantity, signal.reason)
                if trade:
                    trades.append(trade)
            else:
                risk_violations += 1

        elif signal.action == "SELL" and broker.asset > 0:
            trade = broker.sell(bar.close, broker.asset, signal.reason)
            if trade:
                trades.append(trade)

        risk.update(broker.equity)

    broker.mark(bars[-1].close)
    equity_curve.append(broker.equity)
    result = Goal().evaluate(equity_curve, trades, risk_violations)
    return result, trades, equity_curve
