from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, date
from math import sqrt
from statistics import mean
from typing import Any

from .config import settings


@dataclass(frozen=True)
class NotificationPolicy:
    min_oos_accuracy: float = 0.58
    min_rolling_expectancy: float = 0.0
    min_rolling_sample: int = 50
    max_daily_notifications: int = 3
    cooldown_minutes: int = 60


class NotificationGate:
    """Deterministic gate. It can emit an informational notification, never an order."""

    def __init__(self, store, policy: NotificationPolicy | None = None):
        self.store = store
        self.policy = policy or NotificationPolicy(
            min_oos_accuracy=settings.notification_min_oos_accuracy,
            min_rolling_expectancy=settings.notification_min_expectancy,
            min_rolling_sample=settings.notification_min_sample,
            max_daily_notifications=settings.notification_daily_limit,
            cooldown_minutes=settings.notification_cooldown_minutes,
        )

    @staticmethod
    def _wilson_lower_bound(successes: int, total: int, z: float = 1.96) -> float | None:
        if total <= 0:
            return None
        p = successes / total
        denom = 1 + (z * z / total)
        centre = p + (z * z / (2 * total))
        spread = z * sqrt((p * (1 - p) / total) + (z * z / (4 * total * total)))
        return max(0.0, (centre - spread) / denom)

    def empirical_metrics(self, symbol: str, lookback: int = 100) -> dict[str, Any]:
        outcomes = self.store.recent_notification_outcomes(symbol, lookback)
        if not outcomes:
            return {"sample_size": 0, "accuracy": None, "accuracy_lower_bound": None, "expectancy": None}
        hits = [1 if bool(x["correct"]) else 0 for x in outcomes]
        returns = [float(x["realized_return"]) for x in outcomes]
        return {
            "sample_size": len(outcomes),
            "accuracy": mean(hits),
            "accuracy_lower_bound": self._wilson_lower_bound(sum(hits), len(hits)),
            "expectancy": mean(returns),
        }

    def evaluate(
        self,
        *,
        symbol: str,
        strategy_action: str,
        ai_action: str | None,
        risk_approved: bool,
        signal_timestamp: str | None = None,
    ) -> dict[str, Any]:
        metrics = self.empirical_metrics(symbol)
        reasons: list[str] = []
        if strategy_action not in {"BUY", "SELL"}:
            reasons.append("strategy_not_actionable")
        if not risk_approved:
            reasons.append("risk_veto")
        if ai_action not in {None, strategy_action}:
            reasons.append("ai_disagrees")
        if metrics["sample_size"] < self.policy.min_rolling_sample:
            reasons.append("insufficient_empirical_sample")
        elif metrics["accuracy_lower_bound"] < self.policy.min_oos_accuracy:
            reasons.append("oos_accuracy_below_gate")
        if metrics["expectancy"] is None or metrics["expectancy"] <= self.policy.min_rolling_expectancy:
            reasons.append("rolling_expectancy_not_positive")
        if self.store.count_notifications_today(symbol) >= self.policy.max_daily_notifications:
            reasons.append("daily_notification_limit")
        if self.store.notification_in_cooldown(symbol, self.policy.cooldown_minutes):
            reasons.append("cooldown_active")

        eligible = not reasons
        return {
            "eligible": eligible,
            "symbol": symbol,
            "strategy_action": strategy_action,
            "ai_action": ai_action,
            "risk_approved": risk_approved,
            "metrics": metrics,
            "reasons": reasons,
            "signal_timestamp": signal_timestamp,
            "authority": "informational_only",
            "execution_authority": False,
        }

    def create(self, decision: dict[str, Any]) -> dict[str, Any]:
        if not decision["eligible"]:
            return decision
        notification_id = self.store.add_notification(decision)
        return {**decision, "notification_id": notification_id}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
