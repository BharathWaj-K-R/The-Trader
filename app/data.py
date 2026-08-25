from datetime import datetime, timezone
import ccxt
from .models import Bar

class MarketData:
    def __init__(self, name="binance"):
        if name != "binance":
            raise ValueError("Only the Binance public-data adapter is included")
        self.exchange = ccxt.binance({"enableRateLimit": True})

    def fetch(self, symbol: str, timeframe: str, limit: int = 500):
        rows = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        bars, last_ts = [], None
        for ts, op, hi, lo, close, volume in rows:
            values = (ts, op, hi, lo, close, volume)
            if not all(isinstance(x, (int, float)) for x in values):
                continue
            if min(op, hi, lo, close) <= 0 or volume < 0:
                continue
            if hi < max(op, close, lo) or lo > min(op, close, hi):
                continue
            if last_ts is not None and ts <= last_ts:
                continue
            last_ts = ts
            bars.append(Bar(
                timestamp=datetime.fromtimestamp(ts / 1000, tz=timezone.utc),
                open=float(op), high=float(hi), low=float(lo),
                close=float(close), volume=float(volume),
            ))
        if len(bars) < 10:
            raise RuntimeError("Insufficient validated market data")
        return bars
