from datetime import datetime, timezone
from types import SimpleNamespace

from app.ai.schemas import CriticReview, StrategyAnalysis, StrategyProposal
from app.ai.service import StrategyLab
from app.models import StrategyParams


def proposal(**overrides):
    values = {
        "hypothesis": "faster trend response",
        "rationale": "reduce entry latency",
        "fast_window": 18,
        "slow_window": 50,
        "rsi_window": 14,
        "rsi_entry": 56,
        "rsi_exit": 44,
        "use_trend_quality": False,
        "min_trend_gap_pct": 0.0,
        "use_volatility_filter": False,
        "atr_window": 14,
        "min_atr_pct": 0.0,
        "max_atr_pct": 1.0,
        "use_volume_confirmation": False,
        "volume_window": 20,
        "min_volume_ratio": 0.0,
        "risk_notes": ["validate out of sample"],
    }
    values.update(overrides)
    return StrategyProposal(**values)


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
    candidate = proposal()
    critic = CriticReview(
        verdict="approve",
        strengths=["better test score"],
        concerns=[],
        evidence=["walk-forward robust"],
        recommendation="promote",
        confidence=0.9,
    )
    assert analysis.confidence == 0.8
    assert candidate.fast_window < candidate.slow_window
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
            return proposal(hypothesis="reduce latency", rationale="test faster trend response", risk_notes=["validate"]).model_dump(), {}
        return CriticReview(
            verdict=self.verdict, strengths=["candidate"], concerns=[], evidence=["tests"],
            recommendation="promote" if self.verdict == "approve" else "do not promote", confidence=0.8,
        ).model_dump(), {}


def test_evolution_requires_ai_critic_and_deterministic_gates(monkeypatch):
    now = datetime.now(timezone.utc)
    bars = [SimpleNamespace(close=100.0, timestamp=now, open=100.0, high=101.0, low=99.0, volume=1.0) for _ in range(220)]

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
