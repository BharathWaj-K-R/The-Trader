import math

class Goal:
    def __init__(self, min_return=0.03, max_drawdown=0.10, min_trades=5):
        self.min_return = min_return
        self.max_drawdown = max_drawdown
        self.min_trades = min_trades

    def evaluate(self, equity_curve, trades, risk_violations=0):
        if not equity_curve:
            return {"score": 0.0, "success": False, "return_pct": 0.0,
                    "max_drawdown_pct": 0.0, "sharpe_like": 0.0,
                    "trades": 0, "risk_violations": risk_violations}
        start = equity_curve[0]
        end = equity_curve[-1]
        return_pct = end / start - 1 if start else 0.0
        peak = equity_curve[0]
        max_dd = 0.0
        returns = []
        for before, after in zip(equity_curve, equity_curve[1:]):
            peak = max(peak, after)
            max_dd = max(max_dd, 1 - after / peak if peak else 0.0)
            if before:
                returns.append(after / before - 1)
        mean = sum(returns) / len(returns) if returns else 0.0
        variance = sum((r - mean) ** 2 for r in returns) / len(returns) if returns else 0.0
        sharpe_like = mean / math.sqrt(variance) if variance else 0.0
        score = return_pct * 100 + sharpe_like * 2 - max_dd * 50 - risk_violations * 10
        success = (return_pct >= self.min_return and max_dd <= self.max_drawdown
                   and len(trades) >= self.min_trades and risk_violations == 0)
        return {"score": score, "success": success, "return_pct": return_pct,
                "max_drawdown_pct": max_dd, "sharpe_like": sharpe_like,
                "trades": len(trades), "risk_violations": risk_violations}
