from datetime import datetime, timedelta, timezone

from app.models import Bar, StrategyParams
from app.stress import run_cost_sensitivity


def test_cost_sensitivity_returns_all_scenarios():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    bars = []
    for i in range(180):
        price = 100 + (i % 30) * 0.3 + i * 0.05
        bars.append(Bar(start + timedelta(minutes=30 * i), price, price, price, price, 100))
    report = run_cost_sensitivity(bars, StrategyParams(), fee_scenarios=(5, 10), slippage_scenarios=(0, 10))
    assert report["scenarios"] == 4
    assert len(report["results"]) == 4
    assert "worst_case" in report
