from __future__ import annotations

import logging
import time

from .agent import TradingAgent
from .config import settings

logger = logging.getLogger("the_trader.scheduler")


class TradingScheduler:
    """Continuous runtime loop for paper, sandbox, and live execution modes."""

    def __init__(self, agent: TradingAgent, interval_seconds: int | None = None):
        self.agent = agent
        self.interval = interval_seconds or settings.scheduler_interval_seconds
        self.last_reconcile = 0.0

    def tick(self):
        mode = settings.execution_mode
        if mode == "paper":
            result = self.agent.paper_engine().tick()
            logger.info("paper tick action=%s equity=%s", result.get("action"), result.get("equity"))
            return result

        if not self.agent.execution.enabled:
            raise RuntimeError(f"Execution mode {mode} is not available")
        if self.agent.execution.kill_switch:
            logger.warning("execution halted by kill switch")
            return {"action": "HALT", "reason": "kill_switch"}

        result = self.agent.execute_signal()
        logger.info("execution tick result=%s", result)
        now = time.monotonic()
        if now - self.last_reconcile >= settings.live_reconcile_interval_seconds:
            reconciliation = self.agent.reconcile_execution()
            self.last_reconcile = now
            logger.info("reconciliation complete open_orders=%s", len(reconciliation.get("open_orders", [])))
            result["reconciliation"] = reconciliation
        return result

    def run_forever(self):
        logger.info("trading scheduler started mode=%s interval=%ss", settings.execution_mode, self.interval)
        while True:
            started = time.monotonic()
            try:
                self.tick()
            except Exception:
                logger.exception("runtime tick failed")
            elapsed = time.monotonic() - started
            time.sleep(max(1.0, self.interval - elapsed))


def run_scheduler():
    TradingScheduler(TradingAgent()).run_forever()
