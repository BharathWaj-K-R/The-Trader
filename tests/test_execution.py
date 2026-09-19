import os

os.environ.setdefault("EXECUTION_MODE", "paper")

from app.config import settings
from app.execution import LiveExecutionEngine
from app.storage import Store


def test_execution_engine_is_disabled_in_paper(tmp_path):
    store = Store(str(tmp_path / "agent.db"))
    engine = LiveExecutionEngine(store)
    assert engine.enabled is False
    assert engine.status()["mode"] == "paper"
    assert engine.preflight("BTC/USDT")["ready"] is False


def test_execution_controls_persist(tmp_path):
    store = Store(str(tmp_path / "agent.db"))
    account = f"{settings.execution_mode}:{settings.exchange_id}"
    store.save_execution_control(account, True, False, {"high_watermark": 10000})
    saved = store.get_execution_control(account)
    assert saved["armed"] is True
    assert saved["kill_switch"] is False
    assert saved["metadata"]["high_watermark"] == 10000


def test_execution_order_limit_storage(tmp_path):
    store = Store(str(tmp_path / "agent.db"))
    account = "sandbox:binance"
    row_id = store.add_execution_order(account, {
        "symbol": "BTC/USDT",
        "type": "market",
        "side": "buy",
        "amount": 0.001,
        "price": 50000,
        "status": "open",
        "id": "abc123",
    })
    assert row_id > 0
    assert store.count_execution_orders_today(account) == 1
    assert store.recent_execution_orders(account, 1)[0]["exchange_order_id"] == "abc123"
