from datetime import datetime, timedelta, timezone

from app.risk import RiskGuard


def test_daily_loss_resets_on_new_date():
    risk = RiskGuard(1000)
    day1 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    risk.update(1000, day1)
    denied = risk.check(970, 970, 100, 0.2, day1)
    assert denied.reason == "daily_loss_limit"

    day2 = day1 + timedelta(days=1)
    allowed = risk.check(970, 970, 100, 0.2, day2)
    assert allowed.allowed
