from app.goals import Goal


def test_drawdown_is_measured():
    result = Goal().evaluate([100, 110, 90, 95], [], 0)
    assert result["max_drawdown_pct"] > 0


def test_minimum_trades_are_required():
    result = Goal(min_return=0.01, min_trades=2).evaluate([100, 102], [], 0)
    assert result["success"] is False
