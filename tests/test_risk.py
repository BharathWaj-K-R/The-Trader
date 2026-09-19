from app.risk import RiskGuard


def test_position_is_sized_within_cash():
    decision = RiskGuard(10000).check(10000, 10000, 100, 0.20)
    assert decision.allowed
    assert decision.quantity > 0


def test_drawdown_limit_blocks_trading():
    decision = RiskGuard(10000).check(8900, 8900, 100, 0.20)
    assert decision.allowed is False
