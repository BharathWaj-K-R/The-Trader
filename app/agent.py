from .analytics import summarize_equity
from .backtest import run_backtest
from .config import settings
from .data import MarketData
from .models import StrategyParams
from .optimizer import ScientificOptimizer
from .paper import PaperEngine
from .storage import Store
from .walkforward import run_walk_forward


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
        result, trades, equity = run_backtest(market, self.params, settings.initial_capital)
        analytics = summarize_equity(equity, trades)
        run_id = self.store.add_run("backtest", symbol, {
            "bars": len(market), "params": self.params.as_dict(),
            "goal": result, "analytics": analytics,
        })
        for trade in trades:
            self.store.add_trade(run_id, trade)
        return result, trades, analytics

    def improve(self, symbol=None, timeframe=None, bars=500, cycles=5):
        symbol = symbol or settings.symbol
        timeframe = timeframe or settings.timeframe
        market = self.market.fetch(symbol, timeframe, bars)
        self.params, result, history = ScientificOptimizer(self.store, seed=42).improve(
            market, self.params, cycles,
        )
        self.store.add_run("improvement", symbol, {
            "bars": len(market), "cycles": cycles,
            "final_params": self.params.as_dict(), "goal": result,
        })
        return result, history

    def walk_forward(self, symbol=None, timeframe=None, bars=500, folds=4, cycles=6):
        symbol = symbol or settings.symbol
        timeframe = timeframe or settings.timeframe
        market = self.market.fetch(symbol, timeframe, bars)
        report = run_walk_forward(market, self.params, folds=folds, cycles=cycles)
        self.store.add_research_report("walk_forward", symbol, timeframe, report)
        return report

    def paper_engine(self, symbol=None, timeframe=None):
        return PaperEngine(self.store, self.market, symbol=symbol, timeframe=timeframe)
