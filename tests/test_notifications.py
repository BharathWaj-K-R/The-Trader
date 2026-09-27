from app.notifications import NotificationGate, NotificationPolicy


class FakeStore:
    def __init__(self):
        self.outcomes = []
        self.created = 0

    def recent_notification_outcomes(self, symbol, limit):
        return self.outcomes[:limit]

    def count_notifications_today(self, symbol):
        return 0

    def notification_in_cooldown(self, symbol, minutes):
        return False

    def add_notification(self, decision):
        self.created += 1
        return self.created


def test_notification_gate_blocks_without_empirical_sample():
    store = FakeStore()
    gate = NotificationGate(store, NotificationPolicy(min_rolling_sample=50))
    result = gate.evaluate(symbol="SPY", strategy_action="BUY", ai_action=None, risk_approved=True)
    assert result["eligible"] is False
    assert "insufficient_empirical_sample" in result["reasons"]


def test_notification_gate_requires_positive_expectancy():
    store = FakeStore()
    store.outcomes = [{"correct": True, "realized_return": 0.01}] * 50
    gate = NotificationGate(store, NotificationPolicy(min_rolling_sample=50))
    result = gate.evaluate(symbol="SPY", strategy_action="BUY", ai_action=None, risk_approved=True)
    assert result["eligible"] is True
