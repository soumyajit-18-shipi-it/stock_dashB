import yfinance as yf
import pandas as pd
import time
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
        self.last_latency = 0.0

    def get_stock_data(self, ticker: str, range_key: str = "1y") -> pd.DataFrame:
        start_time = time.time()
        cache_key = f"{ticker}_{range_key}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            self.last_latency = (time.time() - start_time) * 1000
            return cached

        period = self.RANGE_MAP.get(range_key, "1y")
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)

        if df.empty:
            self.last_latency = (time.time() - start_time) * 1000
            raise ValueError(f"No data found for ticker: {ticker}")

        self.cache.set(cache_key, df)
        self.last_latency = (time.time() - start_time) * 1000
        return df

    def get_company_info(self, ticker: str) -> Dict[str, Any]:
        start_time = time.time()
        cache_key = f"{ticker}_info"
        cached = self.cache.get(cache_key)
        if cached is not None:
            self.last_latency = (time.time() - start_time) * 1000
            return cached

        stock = yf.Ticker(ticker)
        info = stock.info

        if not info:
            self.last_latency = (time.time() - start_time) * 1000
            return {}

        self.cache.set(cache_key, info)
        self.last_latency = (time.time() - start_time) * 1000
        return info

    def validate_ticker(self, ticker: str) -> bool:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return info is not None and len(info) > 0
        except Exception:
            return False
