from datetime import datetime, timedelta, timezone

from app.models import Bar, StrategyParams
from app.research import run_full_research


def make_bars(n=240):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    bars = []
    for i in range(n):
        cycle = (i % 30) * 0.7
        drift = i * 0.05
        price = 100 + cycle + drift
        ts = start + timedelta(minutes=30 * i)
        bars.append(Bar(ts, price, price, price, price, 100))
    return bars


def test_full_research_has_all_gates():
    report = run_full_research(make_bars(), StrategyParams(), cycles=3, folds=3)
    assert "baseline" in report
    assert "candidate" in report
    assert "walk_forward" in report
    assert "cost_stress" in report
    assert "promotion" in report
    assert len(report["cost_stress"]["results"]) == 12
