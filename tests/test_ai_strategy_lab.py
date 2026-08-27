from types import SimpleNamespace

from app.ai.schemas import CriticReview, StrategyAnalysis, StrategyProposal
from app.ai.service import StrategyLab
from app.models import StrategyParams


def test_structured_ai_schemas_are_valid():
    analysis = StrategyAnalysis(
        verdict="mixed",
        market_regime="trending",
        strengths=["positive excess return"],
        weaknesses=["cost sensitivity"],
        observations=["recent trend"],
        next_experiments=["tighten fast window"],
        confidence=0.8,
    )
    proposal = StrategyProposal(
        hypothesis="faster trend response",
        rationale="reduce entry latency",
        fast_window=18,
        slow_window=50,
        rsi_window=14,
        rsi_entry=56,
        rsi_exit=44,
        risk_notes=["validate out of sample"],
    )
    critic = CriticReview(
        verdict="approve",
        strengths=["better test score"],
        concerns=[],
        evidence=["walk-forward robust"],
        recommendation="promote",
        confidence=0.9,
    )
    assert analysis.confidence == 0.8
    assert proposal.fast_window < proposal.slow_window
    assert critic.verdict == "approve"


class FakeClient:
    def __init__(self, verdict="approve"):
        self.verdict = verdict

    def structured(self, *, system, user, name, schema):
        if name == "strategy_analysis":
            return StrategyAnalysis(
                verdict="mixed", market_regime="trending", strengths=["x"], weaknesses=["y"],
                observations=[], next_experiments=["change fast window"], confidence=0.8,
            ).model_dump(), {}
        if name == "strategy_proposal":
            return StrategyProposal(
                hypothesis="reduce latency", rationale="test faster trend response",
                fast_window=18, slow_window=50, rsi_window=14, rsi_entry=56, rsi_exit=44,
                risk_notes=["validate"],
            ).model_dump(), {}
        return CriticReview(
            verdict=self.verdict, strengths=["candidate"], concerns=[], evidence=["tests"],
            recommendation="promote" if self.verdict == "approve" else "do not promote", confidence=0.8,
        ).model_dump(), {}


def test_evolution_requires_ai_critic_and_deterministic_gates(monkeypatch):
    bars = [SimpleNamespace(close=100.0, timestamp=None, open=100.0, high=101.0, low=99.0, volume=1.0) for _ in range(220)]

    def fake_backtest(bars, params, *args, **kwargs):
        score = 2.0 if params.fast_window == 20 else 4.0
        goal = {"score": score, "return_pct": 0.10 if score > 2 else 0.05, "benchmark_return_pct": 0.02, "excess_return_pct": 0.08 if score > 2 else 0.03, "max_drawdown_pct": 0.04, "risk_violations": 0, "trades": 10}
        trades = []
        equity = [10000.0, 11000.0] if score > 2 else [10000.0, 10500.0]
        return goal, trades, equity

    monkeypatch.setattr("app.ai.service.run_backtest", fake_backtest)
    monkeypatch.setattr("app.ai.service.summarize_equity", lambda equity, trades, prices: {
        "return_pct": equity[-1] / equity[0] - 1, "benchmark_return_pct": 0.02,
        "excess_return_pct": equity[-1] / equity[0] - 1 - 0.02, "max_drawdown_pct": 0.04,
    })
    monkeypatch.setattr("app.ai.service.run_walk_forward", lambda *args, **kwargs: {"robust": True, "positive_folds": 3, "folds_evaluated": 4})
    monkeypatch.setattr("app.ai.service.run_cost_sensitivity", lambda *args, **kwargs: {"scenarios": 12, "robust_scenarios": 8, "results": []})

    baseline = StrategyParams()
    result = StrategyLab(FakeClient("approve")).evolve("BTC/USDT", "30m", bars, baseline)
    assert result["promotion"]["deterministic_gate"] is True
    assert result["promotion"]["promoted"] is True

    blocked = StrategyLab(FakeClient("reject")).evolve("BTC/USDT", "30m", bars, baseline)
    assert blocked["promotion"]["deterministic_gate"] is True
    assert blocked["promotion"]["promoted"] is False
