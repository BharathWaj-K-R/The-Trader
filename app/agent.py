from .analytics import summarize_equity
from .backtest import run_backtest
from .config import settings
from .data import MarketData
from .execution import LiveExecutionEngine
from .models import StrategyParams
from .optimizer import ScientificOptimizer
from .paper import PaperEngine
from .research import run_full_research
from .storage import Store
from .stress import run_cost_sensitivity
from .walkforward import run_walk_forward


class TradingAgent:
    def __init__(self):
        db_path = settings.database_url.replace("sqlite:///", "")
        self.store = Store(db_path)
        self.market = MarketData(settings.data_source)
        active = self.store.active_strategy()
        self.params = StrategyParams(**active["params"]) if active else StrategyParams()
        self.execution = LiveExecutionEngine(self.store)

    @property
    def execution_mode(self):
        return settings.execution_mode

    def backtest(self, symbol=None, timeframe=None, bars=300):
        symbol = symbol or settings.symbol
        timeframe = timeframe or settings.timeframe
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
        symbol = symbol or settings.symbol
        timeframe = timeframe or settings.timeframe
        market = self.market.fetch(symbol, timeframe, bars)
        baseline = StrategyParams(**self.params.as_dict())
        baseline_goal, _, _ = run_backtest(market, baseline, settings.initial_capital)
        candidate, candidate_goal, history = ScientificOptimizer(self.store, seed=42).improve(market, baseline, cycles)
        robustness = run_walk_forward(market, candidate, folds=4, cycles=max(3, min(8, cycles // 2)))
        cost_stress = run_cost_sensitivity(market, candidate)
        promoted = (
            robustness["robust"]
            and cost_stress["robust_scenarios"] >= max(1, cost_stress["scenarios"] // 2)
            and candidate_goal["score"] > baseline_goal["score"]
        )
        if promoted:
            self.params = candidate
            final_goal = candidate_goal
            self.store.activate_strategy(candidate.as_dict(), candidate_goal["score"])
        else:
            self.params = baseline
            final_goal = baseline_goal
            self.store.activate_strategy(baseline.as_dict(), baseline_goal["score"])
        report = {
            "baseline": baseline.as_dict(), "candidate": candidate.as_dict(),
            "baseline_goal": baseline_goal, "candidate_goal": candidate_goal,
            "robustness": robustness, "cost_stress": cost_stress,
            "promoted": promoted, "experiments": history,
        }
        self.store.add_research_report("improvement_gate", symbol, timeframe, report)
        self.store.add_run("improvement", symbol, {
            "bars": len(market), "cycles": cycles,
            "final_params": self.params.as_dict(), "goal": final_goal,
            "promoted": promoted,
        })
        return final_goal, history

    def walk_forward(self, symbol=None, timeframe=None, bars=500, folds=4, cycles=6):
        symbol = symbol or settings.symbol
        timeframe = timeframe or settings.timeframe
        market = self.market.fetch(symbol, timeframe, bars)
        report = run_walk_forward(market, self.params, folds=folds, cycles=cycles)
        self.store.add_research_report("walk_forward", symbol, timeframe, report)
        return report

    def stress_test(self, symbol=None, timeframe=None, bars=500):
        symbol = symbol or settings.symbol
        timeframe = timeframe or settings.timeframe
        market = self.market.fetch(symbol, timeframe, bars)
        report = run_cost_sensitivity(market, self.params)
        self.store.add_research_report("cost_sensitivity", symbol, timeframe, report)
        return report

    def full_research(self, symbol=None, timeframe=None, bars=800, cycles=10, folds=4):
        symbol = symbol or settings.symbol
        timeframe = timeframe or settings.timeframe
        market = self.market.fetch(symbol, timeframe, bars)
        report = run_full_research(market, self.params, cycles=cycles, folds=folds)
        report["symbol"] = symbol
        report["timeframe"] = timeframe
        self.store.add_research_report("full_research", symbol, timeframe, report)
        if report["promotion"]["promoted"]:
            params = StrategyParams(**report["candidate"]["params"])
            self.params = params
            self.store.activate_strategy(params.as_dict(), report["candidate"]["goal"]["score"])
        else:
            self.store.activate_strategy(self.params.as_dict(), report["baseline"]["goal"]["score"])
        return report

    def paper_engine(self, symbol=None, timeframe=None):
        return PaperEngine(self.store, self.market, symbol=symbol, timeframe=timeframe)

    def execution_status(self):
        return self.execution.status()

    def execution_preflight(self, symbol=None):
        return self.execution.preflight(symbol or settings.symbol)

    def arm_execution(self, token):
        return self.execution.arm(token)

    def disarm_execution(self):
        return self.execution.disarm()

    def activate_kill_switch(self):
        return self.execution.activate_kill_switch()

    def reset_kill_switch(self, token):
        return self.execution.reset_kill_switch(token)

    def execute_signal(self, symbol=None, timeframe=None):
        symbol = symbol or settings.symbol
        timeframe = timeframe or settings.timeframe
        from .strategy import MomentumStrategy
        return self.execution.signal_tick(symbol, timeframe, MomentumStrategy(self.params))

    def reconcile_execution(self, symbol=None):
        return self.execution.reconcile(symbol or settings.symbol)
