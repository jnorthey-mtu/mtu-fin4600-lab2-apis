"""Market-data helpers built on the Yahoo Finance v8 *chart* endpoint.

Yahoo has not offered an official, supported API since 2017. The chart endpoint
used below is the one Yahoo's own web pages call. It works without a key but
needs a browser User-Agent, and it can change or be throttled at any time.
Use it for personal / educational purposes and respect Yahoo's terms of service.
"""
from __future__ import annotations

import time

import numpy as np
import pandas as pd

from .http import ApiError, BROWSER_UA, fetch

CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"


def chart_json_to_frame(payload: dict) -> pd.DataFrame:
    """Convert a Yahoo v8 chart JSON payload into a tidy OHLCV DataFrame."""
    result = payload["chart"]["result"][0]
    tz = result["meta"].get("exchangeTimezoneName", "America/New_York")
    q = result["indicators"]["quote"][0]
    df = pd.DataFrame({
        "open": q["open"], "high": q["high"], "low": q["low"],
        "close": q["close"], "volume": q["volume"],
    }, index=pd.to_datetime(result["timestamp"], unit="s", utc=True).tz_convert(tz))
    adj = result["indicators"].get("adjclose")
    df["adj_close"] = adj[0]["adjclose"] if adj else df["close"]
    df.index.name = "date"
    return df.dropna(subset=["close"])


def synthetic_history(symbol: str, days: int = 252, seed: int | None = None) -> pd.DataFrame:
    """SYNTHETIC random-walk prices, used only when the live API is unavailable.
    These are NOT real market prices."""
    rng = np.random.default_rng(seed if seed is not None else abs(hash(symbol)) % 2**32)
    idx = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=days, tz="America/New_York")
    mu, sigma = rng.uniform(-0.1, 0.25), rng.uniform(0.18, 0.55)
    rets = rng.normal(mu / 252, sigma / np.sqrt(252), days)
    close = rng.uniform(20, 300) * np.exp(np.cumsum(rets))
    high = close * (1 + np.abs(rng.normal(0, 0.01, days)))
    low = close * (1 - np.abs(rng.normal(0, 0.01, days)))
    opn = np.clip(close * (1 + rng.normal(0, 0.005, days)), low, high)
    vol = rng.integers(500_000, 20_000_000, days)
    df = pd.DataFrame({"open": opn, "high": high, "low": low, "close": close,
                       "volume": vol, "adj_close": close}, index=idx)
    df.index.name = "date"
    df.attrs["synthetic"] = True
    return df


def yahoo_history(symbol: str, range_: str = "1y", interval: str = "1d",
                  allow_synthetic: bool = True, verbose: bool = False) -> pd.DataFrame:
    """Daily (or intraday) OHLCV history for one symbol from Yahoo's chart endpoint.

    Falls back to clearly-labelled SYNTHETIC data if the network or Yahoo refuses,
    so a class session can keep going. Check df.attrs.get("synthetic").
    """
    url = CHART_URL.format(symbol=symbol)
    params = {"range": range_, "interval": interval, "includeAdjustedClose": "true"}
    try:
        payload = fetch(url, params=params, headers={"User-Agent": BROWSER_UA},
                        ttl=6 * 3600, verbose=verbose)
        df = chart_json_to_frame(payload)
        df.attrs["synthetic"] = False
        return df
    except (ApiError, OSError, KeyError, TypeError, IndexError) as exc:
        if not allow_synthetic:
            raise
        print(f"⚠️  {symbol}: live data unavailable ({type(exc).__name__}: {str(exc)[:70]}). "
              "Using SYNTHETIC prices — not real!")
        return synthetic_history(symbol)


def yahoo_many(symbols, range_: str = "1y", pause: float = 0.4, **kw) -> dict[str, pd.DataFrame]:
    """Fetch several symbols politely (pause between live calls)."""
    out = {}
    for i, s in enumerate(symbols, 1):
        out[s] = yahoo_history(s, range_=range_, **kw)
        flag = " (synthetic)" if out[s].attrs.get("synthetic") else ""
        print(f"[{i:>2}/{len(symbols)}] {s:<6} {len(out[s]):>4} rows{flag}")
        time.sleep(pause)
    return out
