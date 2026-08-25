from .backtest import run_backtest
from .config import settings
from .data import MarketData
from .models import StrategyParams
from .optimizer import ScientificOptimizer
from .storage import Store

class TradingAgent:
    def __init__(self):
        if not settings.paper_only:
            raise RuntimeError("This build is intentionally paper-only")
        db_path = settings.database_url.replace("sqlite:///", "")
        self.store = Store(db_path)
        self.market = MarketData(settings.data_source)
        self.params = StrategyParams()

    def backtest(self, symbol=None, timeframe=None, bars=300):
        symbol = symbol or settings.symbol
        timeframe = timeframe or settings.timeframe
        market = self.market.fetch(symbol, timeframe, bars)
        result, trades, _ = run_backtest(market, self.params, settings.initial_capital)
        run_id = self.store.add_run("backtest", symbol, {
            "bars": len(market), "params": self.params.as_dict(), "goal": result,
        })
        for trade in trades:
            self.store.add_trade(run_id, trade)
        return result, trades

    def improve(self, symbol=None, timeframe=None, bars=500, cycles=5):
        symbol = symbol or settings.symbol
        timeframe = timeframe or settings.timeframe
        market = self.market.fetch(symbol, timeframe, bars)
        self.params, result, history = ScientificOptimizer(self.store).improve(
            market, self.params, cycles,
        )
        self.store.add_run("improvement", symbol, {
            "bars": len(market), "cycles": cycles,
            "final_params": self.params.as_dict(), "goal": result,
        })
        return result, history
