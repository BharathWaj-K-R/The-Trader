from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "paper-only"
    assert body["status"] == "ok"


def test_status():
    response = client.get("/api/status")
    assert response.status_code == 200
    assert response.json()["paper_only"] is True


def test_dashboard():
    response = client.get("/")
    assert response.status_code == 200
    assert "The-Trader" in response.text


def test_invalid_symbol_is_rejected():
    response = client.post("/api/backtest", json={"symbol": "BTCUSDT", "timeframe": "30m", "bars": 60})
    assert response.status_code == 422
