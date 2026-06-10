import yfinance as yf
import pandas as pd
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from .cache import DataCache


class StockDataProvider:
    RANGE_MAP = {
        "1m": "1mo",
        "6m": "6mo",
        "1y": "1y",
        "5y": "5y",
    }

    def __init__(self):
        self.cache = DataCache()

    def get_stock_data(self, ticker: str, range_key: str = "1y") -> pd.DataFrame:
        cache_key = f"{ticker}_{range_key}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        period = self.RANGE_MAP.get(range_key, "1y")
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)

        if df.empty:
            raise ValueError(f"No data found for ticker: {ticker}")

        self.cache.set(cache_key, df)
        return df

    def get_company_info(self, ticker: str) -> Dict[str, Any]:
        cache_key = f"{ticker}_info"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        stock = yf.Ticker(ticker)
        info = stock.info

        profile = {
            "ticker": ticker,
            "name": info.get("longName") or info.get("shortName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "market_cap": info.get("marketCap"),
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "previous_close": info.get("previousClose") or info.get("regularMarketPreviousClose"),
            "currency": info.get("currency"),
            "exchange": info.get("exchange"),
            "country": info.get("country"),
            "week_52_high": info.get("fiftyTwoWeekHigh"),
            "week_52_low": info.get("fiftyTwoWeekLow"),
        }

        self.cache.set(cache_key, profile)
        return profile

    def validate_ticker(self, ticker: str) -> bool:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return info is not None and len(info) > 0
        except Exception:
            return False
