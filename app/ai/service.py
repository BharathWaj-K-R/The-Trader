from __future__ import annotations

import json
from dataclasses import asdict
from statistics import mean
from typing import Any, Type

from .client import GrokClient, GrokError
from .schemas import (
    AnomalyAssessment,
    CriticReview,
    RegimeAssessment,
    StrategyAnalysis,
    StrategyProposal,
    TradeJournalEntry,
)
from ..analytics import summarize_equity
from ..backtest import run_backtest
from ..models import StrategyParams
from ..stress import run_cost_sensitivity
from ..walkforward import run_walk_forward


SYSTEM = """You are the research scientist inside The-Trader. You analyze evidence, generate falsifiable hypotheses, and never claim guaranteed profit. The deterministic research engine is the judge. Never recommend bypassing risk controls, live execution gates, or validation. Prefer simple, interpretable changes and explicitly discuss uncertainty."""


def _schema(model: Type[Any]) -> dict[str, Any]:
    return model.model_json_schema()


def _bars_context(bars: list[Any]) -> dict[str, Any]:
    closes = [b.close for b in bars]
    recent = [
        {"time": b.timestamp.isoformat(), "open": b.open, "high": b.high, "low": b.low, "close": b.close, "volume": b.volume}
        for b in bars[-20:]
    ]
    return {
        "count": len(bars),
        "first_close": closes[0] if closes else None,
        "last_close": closes[-1] if closes else None,
        "simple_change": (closes[-1] / closes[0] - 1) if len(closes) >= 2 and closes[0] else 0,
        "average_volume": mean([b.volume for b in bars[-20:]]) if bars else 0,
        "recent": recent,
    }


class StrategyLab:
    def __init__(self, client: GrokClient | None = None):
        self.client = client or GrokClient()

    def _call(self, model: Type[Any], name: str, prompt: str) -> tuple[Any, dict[str, Any]]:
        value, usage = self.client.structured(system=SYSTEM, user=prompt, name=name, schema=_schema(model))
        return model.model_validate(value), usage

    def analyze(self, symbol: str, timeframe: str, bars: list[Any], params: StrategyParams, baseline: dict[str, Any], recent_experiments: list[dict[str, Any]] | None = None):
        payload = {
            "symbol": symbol,
            "timeframe": timeframe,
            "strategy": params.as_dict(),
            "baseline_metrics": baseline,
            "market": _bars_context(bars),
            "recent_experiments": (recent_experiments or [])[:12],
        }
        return self._call(StrategyAnalysis, "strategy_analysis", "Analyze the current deterministic strategy and identify evidence-backed weaknesses and high-value experiments. Return only the schema.\n\n" + json.dumps(payload, default=str))

    def propose(self, symbol: str, timeframe: str, bars: list[Any], params: StrategyParams, analysis: StrategyAnalysis):
        payload = {
            "symbol": symbol,
            "timeframe": timeframe,
            "current_strategy": params.as_dict(),
            "analysis": analysis.model_dump(),
            "market": _bars_context(bars),
            "constraints": {
                "fast_window": [5, 60], "slow_window": [10, 150], "rsi_window": [5, 30],
                "rsi_entry": [50, 70], "rsi_exit": [30, 50], "fast_less_than_slow": True,
            },
        }
        return self._call(StrategyProposal, "strategy_proposal", "Propose exactly one small, testable parameter-level improvement to the existing strategy. Do not invent unavailable indicators. Stay within the stated parameter bounds. Return only the schema.\n\n" + json.dumps(payload, default=str))

    def critic(self, candidate: dict[str, Any], baseline: dict[str, Any], walk_forward: dict[str, Any], cost_stress: dict[str, Any], analysis: StrategyAnalysis, proposal: StrategyProposal):
        payload = {
            "baseline": baseline,
            "candidate": candidate,
            "walk_forward": walk_forward,
            "cost_stress_summary": {
                "scenarios": cost_stress.get("scenarios"),
                "profitable_scenarios": cost_stress.get("profitable_scenarios"),
                "robust_scenarios": cost_stress.get("robust_scenarios"),
                "worst_case": cost_stress.get("worst_case"),
            },
            "analysis": analysis.model_dump(),
            "proposal": proposal.model_dump(),
        }
        return self._call(CriticReview, "critic_review", "Act as an adversarial research critic. Decide whether the candidate deserves promotion based only on the evidence. Reject fragile improvements and demand robust out-of-sample and cost behavior. Return only the schema.\n\n" + json.dumps(payload, default=str))

    def regime(self, symbol: str, timeframe: str, bars: list[Any], strategy_metrics: dict[str, Any]):
        payload = {"symbol": symbol, "timeframe": timeframe, "market": _bars_context(bars), "strategy_metrics": strategy_metrics}
        return self._call(RegimeAssessment, "regime_assessment", "Classify the current market regime from the supplied evidence and explain how it affects the deterministic strategy. Do not forecast a guaranteed future price. Return only the schema.\n\n" + json.dumps(payload, default=str))

    def anomaly(self, symbol: str, timeframe: str, bars: list[Any], recent_trades: list[dict[str, Any]], execution_state: dict[str, Any]):
        payload = {"symbol": symbol, "timeframe": timeframe, "market": _bars_context(bars), "recent_trades": recent_trades[-25:], "execution": execution_state}
        return self._call(AnomalyAssessment, "anomaly_assessment", "Look for operational or strategy anomalies. Prefer concrete observable evidence. Recommend disarm or review when execution behavior looks unsafe. Return only the schema.\n\n" + json.dumps(payload, default=str))

    def journal(self, trade: dict[str, Any], strategy: dict[str, Any], market: dict[str, Any]):
        payload = {"trade": trade, "strategy": strategy, "market": market}
        return self._call(TradeJournalEntry, "trade_journal", "Explain one completed trade as an audit-friendly journal entry. Separate expected behavior from observed outcome and avoid hindsight claims. Return only the schema.\n\n" + json.dumps(payload, default=str))

    def evolve(self, symbol: str, timeframe: str, bars: list[Any], params: StrategyParams, recent_experiments: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        baseline_goal, baseline_trades, baseline_equity = run_backtest(bars, params)
        baseline_analytics = summarize_equity(baseline_equity, baseline_trades, [b.close for b in bars])
        analysis, usage_a = self.analyze(symbol, timeframe, bars, params, {"goal": baseline_goal, "analytics": baseline_analytics}, recent_experiments)
        proposal, usage_p = self.propose(symbol, timeframe, bars, params, analysis)
        candidate_params = StrategyParams(
            fast_window=proposal.fast_window,
            slow_window=proposal.slow_window,
            rsi_window=proposal.rsi_window,
            rsi_entry=proposal.rsi_entry,
            rsi_exit=proposal.rsi_exit,
        )
        if candidate_params.fast_window >= candidate_params.slow_window:
            raise GrokError("Grok proposed invalid strategy ordering")
        candidate_goal, candidate_trades, candidate_equity = run_backtest(bars, candidate_params)
        candidate_analytics = summarize_equity(candidate_equity, candidate_trades, [b.close for b in bars])
        walk_forward = run_walk_forward(bars, candidate_params, folds=4, cycles=4)
        cost_stress = run_cost_sensitivity(bars, candidate_params)
        critic, usage_c = self.critic(
            {"params": candidate_params.as_dict(), "goal": candidate_goal, "analytics": candidate_analytics},
            {"params": params.as_dict(), "goal": baseline_goal, "analytics": baseline_analytics},
            walk_forward,
            cost_stress,
            analysis,
            proposal,
        )
        deterministic_gate = (
            walk_forward["robust"]
            and cost_stress["robust_scenarios"] >= max(1, cost_stress["scenarios"] // 2)
            and candidate_goal["score"] > baseline_goal["score"]
            and candidate_goal["excess_return_pct"] >= baseline_goal["excess_return_pct"]
        )
        promoted = deterministic_gate and critic.verdict == "approve"
        return {
            "analysis": analysis.model_dump(),
            "proposal": proposal.model_dump(),
            "baseline": {"params": params.as_dict(), "goal": baseline_goal, "analytics": baseline_analytics},
            "candidate": {"params": candidate_params.as_dict(), "goal": candidate_goal, "analytics": candidate_analytics},
            "walk_forward": walk_forward,
            "cost_stress": {k: v for k, v in cost_stress.items() if k != "results"} | {"results": cost_stress["results"][:24]},
            "critic": critic.model_dump(),
            "promotion": {"promoted": promoted, "deterministic_gate": deterministic_gate, "reason": "AI critic approved and deterministic gates passed" if promoted else "Promotion blocked by deterministic or AI critic gate"},
            "usage": {"analysis": usage_a, "proposal": usage_p, "critic": usage_c},
        }
