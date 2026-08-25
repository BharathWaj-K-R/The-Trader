from app.goals import Goal


def test_goal_exposes_benchmark_and_excess_return():
    result = Goal(min_return=0.01, min_trades=0).evaluate([100, 105], [], 0, benchmark_return=0.02)
    assert result["return_pct"] == 0.05
    assert result["benchmark_return_pct"] == 0.02
    assert result["excess_return_pct"] == 0.03
