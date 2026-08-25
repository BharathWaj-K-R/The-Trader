from __future__ import annotations

import logging
import time

from .agent import TradingAgent
from .config import settings

logger = logging.getLogger("the_trader.scheduler")


class PaperScheduler:
    """Small dependency-free scheduler for continuous paper ticks."""

    def __init__(self, agent: TradingAgent, interval_seconds: int | None = None):
        self.agent = agent
        self.interval = interval_seconds or settings.scheduler_interval_seconds

    def run_forever(self):
        logger.info("paper scheduler started interval=%ss", self.interval)
        while True:
            started = time.monotonic()
            try:
                result = self.agent.paper_engine().tick()
                logger.info("paper tick action=%s equity=%s", result.get("action"), result.get("equity"))
            except Exception:
                logger.exception("paper tick failed")
            elapsed = time.monotonic() - started
            time.sleep(max(1.0, self.interval - elapsed))


def run_scheduler():
    PaperScheduler(TradingAgent()).run_forever()
