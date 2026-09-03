"""Market data fetching via yfinance."""

from dataclasses import dataclass
from typing import Optional

import yfinance as yf


@dataclass
class Quote:
    ticker: str
    price: float
    prev_close: float
    day_high: float
    day_low: float
    volume: int
    avg_volume_10d: Optional[float]
    week52_high: float
    week52_low: float
    ma50: Optional[float]
    ma200: Optional[float]
    market_cap: Optional[float]
    pe_ratio: Optional[float]

    @property
    def change(self) -> float:
        return self.price - self.prev_close

    @property
    def change_pct(self) -> float:
        if not self.prev_close:
            return 0.0
        return (self.change / self.prev_close) * 100


def fetch_quote(ticker: str) -> Quote:
    """Fetch a snapshot quote + technicals for a single ticker."""
    tk = yf.Ticker(ticker)
    info = tk.info or {}
    hist = tk.history(period="1y")

    price = info.get("currentPrice") or info.get("regularMarketPrice")
    prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose")
    day_high = info.get("dayHigh") or info.get("regularMarketDayHigh")
    day_low = info.get("dayLow") or info.get("regularMarketDayLow")
    volume = info.get("volume") or info.get("regularMarketVolume") or 0
    avg_volume_10d = info.get("averageVolume10days")
    week52_high = info.get("fiftyTwoWeekHigh")
    week52_low = info.get("fiftyTwoWeekLow")
    market_cap = info.get("marketCap")
    pe_ratio = info.get("trailingPE")

    ma50 = None
    ma200 = None
    if not hist.empty:
        if price is None:
            price = float(hist["Close"].iloc[-1])
        if prev_close is None and len(hist) > 1:
            prev_close = float(hist["Close"].iloc[-2])
        if day_high is None:
            day_high = float(hist["High"].iloc[-1])
        if day_low is None:
            day_low = float(hist["Low"].iloc[-1])
        if len(hist) >= 50:
            ma50 = float(hist["Close"].tail(50).mean())
        if len(hist) >= 200:
            ma200 = float(hist["Close"].tail(200).mean())
        if week52_high is None:
            week52_high = float(hist["High"].max())
        if week52_low is None:
            week52_low = float(hist["Low"].min())

    return Quote(
        ticker=ticker.upper(),
        price=float(price or 0.0),
        prev_close=float(prev_close or 0.0),
        day_high=float(day_high or 0.0),
        day_low=float(day_low or 0.0),
        volume=int(volume or 0),
        avg_volume_10d=avg_volume_10d,
        week52_high=float(week52_high or 0.0),
        week52_low=float(week52_low or 0.0),
        ma50=ma50,
        ma200=ma200,
        market_cap=market_cap,
        pe_ratio=pe_ratio,
    )
