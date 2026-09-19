from datetime import datetime, timedelta, timezone

from app.models import Bar, StrategyParams
from app.walkforward import run_walk_forward


def make_bars(n=220):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    out = []
    price = 100.0
    for i in range(n):
        price += 0.15 if (i // 15) % 2 == 0 else -0.08
        out.append(Bar(start + timedelta(minutes=30 * i), price, price, price, price, 100))
    return out


def test_walk_forward_produces_out_of_sample_folds():
    report = run_walk_forward(make_bars(), StrategyParams(), folds=4, cycles=2)
    assert report["folds_evaluated"] == 3
    assert len(report["fold_results"]) == 3
    assert all("test_score" in row for row in report["fold_results"])
