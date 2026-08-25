from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["mode"] == "paper-only"


def test_status():
    response = client.get("/api/status")
    assert response.status_code == 200
    assert response.json()["paper_only"] is True
