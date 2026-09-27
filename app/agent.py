from .analytics import summarize_equity
from .backtest import run_backtest
from .config import settings
from .data import MarketData
from .models import StrategyParams
from .optimizer import ScientificOptimizer
from .paper import PaperEngine
from .research import run_full_research
from .storage import Store
from .stress import run_cost_sensitivity
from .walkforward import run_walk_forward
from .v4 import validate_universe


class TradingAgent:
    """v4.0 research and paper-trading orchestrator. No live execution boundary exists."""

    def __init__(self):
        db_path = settings.database_url.replace("sqlite:///", "")
        self.store = Store(db_path)
        self.market = MarketData(settings.data_source)
        active = self.store.active_strategy()
        self.params = StrategyParams(**active["params"]) if active else StrategyParams()

    @property
    def execution_mode(self):
        return "paper"

    def _scope(self, symbol=None, timeframe=None):
        return validate_universe(symbol or settings.symbol, timeframe or settings.timeframe)

    def backtest(self, symbol=None, timeframe=None, bars=300):
        symbol, timeframe = self._scope(symbol, timeframe)
        market = self.market.fetch(symbol, timeframe, bars)
        result, trades, equity = run_backtest(market, self.params, settings.initial_capital)
        analytics = summarize_equity(equity, trades, [bar.close for bar in market])
        run_id = self.store.add_run("backtest", symbol, {
            "bars": len(market), "start": market[0].timestamp.isoformat(),
            "end": market[-1].timestamp.isoformat(), "params": self.params.as_dict(),
            "goal": result, "analytics": analytics,
        })
        for trade in trades:
            self.store.add_trade(run_id, trade)
        return result, trades, analytics

    def improve(self, symbol=None, timeframe=None, bars=700, cycles=10):
        symbol, timeframe = self._scope(symbol, timeframe)
        market = self.market.fetch(symbol, timeframe, bars)
        baseline = StrategyParams(**self.params.as_dict())
        baseline_goal, _, _ = run_backtest(market, baseline, settings.initial_capital)
        candidate, candidate_goal, history = ScientificOptimizer(seed=42).improve(market, baseline, cycles)
        robustness = run_walk_forward(market, candidate, folds=4, cycles=max(3, min(8, cycles // 2)))
        cost_stress = run_cost_sensitivity(market, candidate)
        promoted = (
            robustness["robust"]
            and cost_stress["robust_scenarios"] >= max(1, cost_stress["scenarios"] // 2)
            and candidate_goal["score"] > baseline_goal["score"]
        )
        final = candidate if promoted else baseline
        self.params = final
        self.store.activate_strategy(final.as_dict(), (candidate_goal if promoted else baseline_goal)["score"])
        self.store.add_research_report("improvement_gate", symbol, timeframe, {
            "baseline": baseline.as_dict(), "candidate": candidate.as_dict(),
            "baseline_goal": baseline_goal, "candidate_goal": candidate_goal,
            "robustness": robustness, "cost_stress": cost_stress,
            "promoted": promoted, "experiments": history,
        })
        return (candidate_goal if promoted else baseline_goal), history

    def walk_forward(self, symbol=None, timeframe=None, bars=500, folds=4, cycles=6):
        symbol, timeframe = self._scope(symbol, timeframe)
        market = self.market.fetch(symbol, timeframe, bars)
        report = run_walk_forward(market, self.params, folds=folds, cycles=cycles)
        self.store.add_research_report("walk_forward", symbol, timeframe, report)
        return report

    def stress_test(self, symbol=None, timeframe=None, bars=500):
        symbol, timeframe = self._scope(symbol, timeframe)
        market = self.market.fetch(symbol, timeframe, bars)
        report = run_cost_sensitivity(market, self.params)
        self.store.add_research_report("cost_sensitivity", symbol, timeframe, report)
        return report

    def full_research(self, symbol=None, timeframe=None, bars=800, cycles=10, folds=4):
        symbol, timeframe = self._scope(symbol, timeframe)
        market = self.market.fetch(symbol, timeframe, bars)
        report = run_full_research(market, self.params, symbol=symbol, timeframe=timeframe, cycles=cycles, folds=folds)
        self.store.add_research_report("full_research", symbol, timeframe, report)
        if report["promotion"]["promoted"]:
            params = StrategyParams(**report["candidate"]["params"])
            self.params = params
            self.store.activate_strategy(params.as_dict(), report["candidate"]["goal"]["score"])
        else:
            self.store.activate_strategy(self.params.as_dict(), report["baseline"]["goal"]["score"])
        return report

    def paper_engine(self, symbol=None, timeframe=None):
        symbol, timeframe = self._scope(symbol, timeframe)
        return PaperEngine(self.store, self.market, symbol=symbol, timeframe=timeframe)

    def execution_status(self):
        return {
            "mode": "paper",
            "live_enabled": False,
            "sandbox_enabled": False,
            "armed": False,
            "kill_switch": True,
            "execution_authority": "paper_only",
            "enabled": False,
        }

    def execution_preflight(self, symbol=None):
        symbol, timeframe = self._scope(symbol, settings.timeframe)
        return {
            "ok": True,
            "mode": "paper",
            "symbol": symbol,
            "timeframe": timeframe,
            "live_execution": False,
            "reason": "v4.0 live trading is out of scope",
        }

    def arm_execution(self, token=""):
        raise RuntimeError("v4.0 has no exchange execution authority")

    def disarm_execution(self):
        return {"armed": False, "mode": "paper"}

    def activate_kill_switch(self):
        return {"armed": False, "kill_switch": True, "mode": "paper"}

    def reset_kill_switch(self, token=""):
        raise RuntimeError("v4.0 kill switch reset is not an exchange control")

    def execute_signal(self, symbol=None, timeframe=None):
        symbol, timeframe = self._scope(symbol, timeframe)
        result = self.paper_engine(symbol, timeframe).tick()
        result["execution_authority"] = False
        return result

    def reconcile_execution(self, symbol=None):
        symbol, timeframe = self._scope(symbol, settings.timeframe)
        return {
            "mode": "paper",
            "symbol": symbol,
            "timeframe": timeframe,
            "exchange_reconciliation": False,
            "reason": "no live or sandbox broker exists in v4.0",
        }
