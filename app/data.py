from datetime import timezone
import math

import pandas as pd
import yfinance as yf

from .models import Bar


class MarketData:
    """Validated Yahoo Finance adapter for the frozen v4.0 initial universe."""

    ALLOWED = {"SPY", "QQQ"}
    TIMEFRAME = "1h"

    def __init__(self, name="yfinance"):
        if name != "yfinance":
            raise ValueError("v4 primary market data source is yfinance")

    def fetch(self, symbol: str, timeframe: str, limit: int = 500):
        symbol = symbol.strip().upper()
        if symbol not in self.ALLOWED:
            raise ValueError("v4 universe is limited to SPY and QQQ")
        if timeframe != self.TIMEFRAME:
            raise ValueError("v4 initial timeframe is fixed to 1h")
        limit = max(60, min(int(limit), 1500))

        # Yahoo intraday history is constrained; 1h data is sufficient for the v4
        # initial research window and avoids pretending older intraday data exists.
        frame = yf.download(
            symbol,
            period="60d",
            interval="1h",
            auto_adjust=False,
            progress=False,
            threads=False,
            group_by="column",
            multi_level_index=False,
        )
        if frame is None or frame.empty:
            raise RuntimeError("Yahoo Finance returned no market data")

        if isinstance(frame.columns, pd.MultiIndex):
            frame.columns = [c[0] if isinstance(c, tuple) else c for c in frame.columns]

        required = {"Open", "High", "Low", "Close", "Volume"}
        missing = required - set(frame.columns)
        if missing:
            raise RuntimeError(f"Yahoo Finance data missing columns: {sorted(missing)}")

        frame = frame.dropna(subset=list(required)).sort_index()
        bars: list[Bar] = []
        last_ts = None
        for index, row in frame.tail(limit).iterrows():
            ts = pd.Timestamp(index)
            if ts.tzinfo is None:
                ts = ts.tz_localize("UTC")
            else:
                ts = ts.tz_convert(timezone.utc)
            values = [float(row[c]) for c in ("Open", "High", "Low", "Close", "Volume")]
            op, hi, lo, close, volume = values
            if not all(math.isfinite(v) for v in values):
                continue
            if min(op, hi, lo, close) <= 0 or volume < 0:
                continue
            if hi < max(op, close, lo) or lo > min(op, close, hi):
                continue
            if last_ts is not None and ts <= last_ts:
                continue
            last_ts = ts
            bars.append(
                Bar(
                    timestamp=ts.to_pydatetime(),
                    open=op,
                    high=hi,
                    low=lo,
                    close=close,
                    volume=volume,
                )
            )

        if len(bars) < 60:
            raise RuntimeError(f"Insufficient validated Yahoo Finance bars: {len(bars)}")
        return bars
