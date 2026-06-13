import logging
import time
from typing import Any, cast
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from data.cache import DataCache

logger = logging.getLogger("stock_dashboard")

class StockDataProvider:
    RANGE_MAP = {
        "1m": "1mo",
        "6m": "6mo",
        "1y": "1y",
        "5y": "5y",
    }

    def __init__(self) -> None:
        self.cache = DataCache()
        self.last_latency = 0.0
        self.session = requests.Session()
        
        # Configure retries with exponential backoff
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        })

    def get_stock_data(self, ticker: str, range_key: str = "1y", force_refresh: bool = False) -> pd.DataFrame:
        start_time = time.time()
        cache_key = f"{ticker}_{range_key}"
        
        if not force_refresh:
            cached = self.cache.get(cache_key)
            if cached is not None and isinstance(cached, pd.DataFrame):
                self.last_latency = (time.time() - start_time) * 1000
                return cached

        period = self.RANGE_MAP.get(range_key, "1y")
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range={period}&interval=1d"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()

            if not data.get("chart", {}).get("result"):
                raise ValueError(f"No results found for ticker: {ticker}")

            result = data["chart"]["result"][0]
            meta = result.get("meta", {})
            timestamps = result.get("timestamp", [])
            indicators = result.get("indicators", {}).get("quote", [{}])[0]

            if not timestamps:
                raise ValueError(f"No historical data found for ticker: {ticker}")

            df = pd.DataFrame(
                {
                    "Open": indicators.get("open", []),
                    "High": indicators.get("high", []),
                    "Low": indicators.get("low", []),
                    "Close": indicators.get("close", []),
                    "Volume": indicators.get("volume", []),
                },
                index=pd.to_datetime(timestamps, unit="s"),
            )

            df.index.name = "Date"
            df.attrs["metadata"] = {
                "longName": meta.get("longName") or meta.get("shortName"),
                "currency": meta.get("currency"),
                "regularMarketPrice": meta.get("regularMarketPrice"),
            }

            df = df.dropna(how="any")
            if df.empty:
                raise ValueError(f"No valid data points for ticker: {ticker}")

            self.cache.set(cache_key, df)
            self.last_latency = (time.time() - start_time) * 1000
            return df

        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {str(e)}")
            raise ValueError(f"Error fetching data for {ticker}: {str(e)}") from e

    def get_company_info(self, ticker: str) -> dict[str, Any]:
        start_time = time.time()
        cache_key = f"{ticker}_info"
        cached = self.cache.get(cache_key)
        if cached is not None and isinstance(cached, dict):
            self.last_latency = (time.time() - start_time) * 1000
            return cast(dict[str, Any], cached)

        info: dict[str, Any] = {}
        try:
            url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={ticker}"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("quoteResponse", {}).get("result"):
                    quote = data["quoteResponse"]["result"][0]
                    info = {
                        "sector": quote.get("sector"),
                        "industry": quote.get("industry"),
                        "marketCap": quote.get("marketCap"),
                        "previousClose": quote.get("regularMarketPreviousClose"),
                        "longName": quote.get("longName"),
                    }
        except Exception as e:
            logger.warning(f"Error fetching info for {ticker}: {e}")

        self.cache.set(cache_key, info)
        self.last_latency = (time.time() - start_time) * 1000
        return info
