from __future__ import annotations

from pydantic import BaseModel, Field


class StrategyAnalysis(BaseModel):
    verdict: str = Field(description="promising, weak, or mixed")
    market_regime: str
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    observations: list[str] = Field(default_factory=list)
    next_experiments: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)


class StrategyProposal(BaseModel):
    hypothesis: str
    rationale: str
    fast_window: int = Field(ge=5, le=60)
    slow_window: int = Field(ge=10, le=150)
    rsi_window: int = Field(ge=5, le=30)
    rsi_entry: float = Field(ge=50, le=70)
    rsi_exit: float = Field(ge=30, le=50)
    use_trend_quality: bool
    min_trend_gap_pct: float = Field(ge=0, le=0.10)
    use_volatility_filter: bool
    atr_window: int = Field(ge=2, le=60)
    min_atr_pct: float = Field(ge=0, le=1)
    max_atr_pct: float = Field(gt=0, le=1)
    use_volume_confirmation: bool
    volume_window: int = Field(ge=2, le=100)
    min_volume_ratio: float = Field(ge=0, le=5)
    risk_notes: list[str] = Field(default_factory=list)


class CriticReview(BaseModel):
    verdict: str = Field(description="approve, review, or reject")
    strengths: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    recommendation: str
    confidence: float = Field(ge=0, le=1)


class RegimeAssessment(BaseModel):
    regime: str
    trend_strength: float = Field(ge=0, le=1)
    volatility_state: str
    observations: list[str] = Field(default_factory=list)
    strategy_implication: str
    confidence: float = Field(ge=0, le=1)


class AnomalyAssessment(BaseModel):
    anomalous: bool
    severity: str
    signals: list[str] = Field(default_factory=list)
    likely_causes: list[str] = Field(default_factory=list)
    recommended_action: str
    confidence: float = Field(ge=0, le=1)


class TradeJournalEntry(BaseModel):
    summary: str
    expected_behavior: str
    what_happened: str
    lessons: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
