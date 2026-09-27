from __future__ import annotations

import logging
import time

from .agent import TradingAgent
from .config import settings

logger = logging.getLogger("the_trader.scheduler")


class TradingScheduler:
    """v4.0 paper scheduler. It never submits exchange orders."""

    def __init__(self, agent: TradingAgent, interval_seconds: int | None = None):
        self.agent = agent
        self.interval = interval_seconds or settings.scheduler_interval_seconds

    def tick(self):
        results = []
        for symbol in ("SPY", "QQQ"):
            try:
                result = self.agent.paper_engine(symbol, "1h").tick()
                results.append({"symbol": symbol, **result})
            except Exception as exc:
                logger.exception("paper tick failed for %s", symbol)
                results.append({"symbol": symbol, "action": "ERROR", "error": str(exc)})
        return {"mode": "paper", "results": results, "execution_authority": False}

    def run_forever(self):
        logger.info("THE TRADER v4.0 paper scheduler started interval=%ss", self.interval)
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
