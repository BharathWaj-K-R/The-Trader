from datetime import datetime, timedelta, timezone

from app.models import Bar
from app.paper import PaperEngine
from app.storage import Store


class FakeMarket:
    def __init__(self, bars):
        self.bars = bars

    def fetch(self, symbol, timeframe, limit):
        return self.bars[-limit:]


def bars(n=120):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    out = []
    for i in range(n):
        price = 100 + i * 0.25
        out.append(Bar(start + timedelta(minutes=30 * i), price, price, price, price, 100))
    return out


def test_paper_state_survives_engine_restart(tmp_path):
    store = Store(str(tmp_path / "agent.db"))
    market = FakeMarket(bars())
    first = PaperEngine(store, market, "BTC/USDT", "30m")
    first.tick()
    before = first.snapshot()

    second = PaperEngine(store, market, "BTC/USDT", "30m")
    after = second.snapshot()
    assert after["cash"] == before["cash"]
    assert after["asset"] == before["asset"]
    assert after["realized_pnl"] == before["realized_pnl"]
