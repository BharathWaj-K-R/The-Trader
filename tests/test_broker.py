from app.broker import PaperBroker


def test_realized_pnl_is_profit_not_proceeds(monkeypatch):
    broker = PaperBroker(1000)
    buy = broker.buy(100, 5, "entry")
    assert buy is not None
    sell = broker.sell(120, 5, "exit")
    assert sell is not None
    assert sell.pnl > 0
    assert abs(sell.pnl - (broker.realized_pnl)) < 1e-9
    assert broker.asset == 0
    assert broker.cost_basis == 0
