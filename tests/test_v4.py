import pytest

from app.config import Settings
from app.v4 import product_manifest, safety_manifest, validate_universe


def test_v4_scope_is_fixed():
    assert validate_universe("SPY", "1h") == ("SPY", "1h")
    assert validate_universe("QQQ", "1h") == ("QQQ", "1h")
    with pytest.raises(ValueError):
        validate_universe("BTC/USDT", "30m")
    with pytest.raises(ValueError):
        validate_universe("SPY", "1d")


def test_v4_manifest_disables_live_execution():
    manifest = product_manifest()
    safety = safety_manifest()
    assert manifest["specification"] == "v4.0"
    assert manifest["live_trading"] is False
    assert safety["autonomous_ai_execution"] is False
    assert safety["risk_veto"] is True


def test_settings_reject_non_paper():
    with pytest.raises(ValueError):
        Settings(execution_mode="live")
