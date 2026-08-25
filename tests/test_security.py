import pytest
from fastapi import HTTPException

from app.config import settings
from app.security import require_api_key


def test_production_requires_api_key(monkeypatch):
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "api_key", "secret")
    with pytest.raises(HTTPException) as exc:
        require_api_key(None)
    assert exc.value.status_code == 401
    require_api_key("secret")


def test_development_allows_anonymous(monkeypatch):
    monkeypatch.setattr(settings, "environment", "development")
    monkeypatch.setattr(settings, "api_key", None)
    require_api_key(None)
