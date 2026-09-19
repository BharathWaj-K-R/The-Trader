from __future__ import annotations

from math import sqrt


def summarize_equity(equity_curve, trades=None, prices=None):
    values = list(equity_curve or [])
    trades = list(trades or [])
    prices = list(prices or [])
    if not values:
        return {
            "start_equity": 0.0,
            "end_equity": 0.0,
            "return_pct": 0.0,
            "benchmark_return_pct": 0.0,
            "excess_return_pct": 0.0,
            "max_drawdown_pct": 0.0,
            "volatility_like": 0.0,
            "win_rate_pct": 0.0,
            "profit_factor": 0.0,
            "realized_pnl": 0.0,
            "trade_count": len(trades),
        }

    start = float(values[0])
    end = float(values[-1])
    peak = start
    max_drawdown = 0.0
    returns = []
    for before, after in zip(values, values[1:]):
        peak = max(peak, after)
        if peak:
            max_drawdown = max(max_drawdown, 1 - after / peak)
        if before:
            returns.append(after / before - 1)

    mean = sum(returns) / len(returns) if returns else 0.0
    variance = sum((r - mean) ** 2 for r in returns) / len(returns) if returns else 0.0
    volatility = sqrt(variance) if variance else 0.0

    sells = [float(t.pnl) for t in trades if getattr(t, "side", "") == "SELL"]
    winners = [p for p in sells if p > 0]
    losers = [abs(p) for p in sells if p < 0]
    gross_profit = sum(winners)
    gross_loss = sum(losers)

    benchmark = ((prices[-1] / prices[0]) - 1) if len(prices) >= 2 and prices[0] else 0.0
    strategy_return = (end / start - 1) if start else 0.0

    return {
        "start_equity": start,
        "end_equity": end,
        "return_pct": strategy_return,
        "benchmark_return_pct": benchmark,
        "excess_return_pct": strategy_return - benchmark,
        "max_drawdown_pct": max_drawdown,
        "volatility_like": volatility,
        "win_rate_pct": (len(winners) / len(sells) * 100) if sells else 0.0,
        "profit_factor": (gross_profit / gross_loss) if gross_loss else (999.0 if gross_profit else 0.0),
        "realized_pnl": sum(sells),
        "trade_count": len(trades),
    }
