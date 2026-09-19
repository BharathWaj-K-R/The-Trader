from app.models import StrategyParams
from app.storage import Store


def test_active_strategy_round_trip(tmp_path):
    store = Store(str(tmp_path / "agent.db"))
    params = StrategyParams(fast_window=12, slow_window=40, rsi_entry=58, rsi_exit=42)
    store.activate_strategy(params.as_dict(), 3.14)

    restored = store.active_strategy()
    assert restored["params"] == params.as_dict()
    assert restored["score"] == 3.14
