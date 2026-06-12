import time
from typing import Any

import pandas as pd
import requests
from data.cache import DataCache


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
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self._crumb = None

    def _get_crumb(self) -> str:
        if self._crumb:
            return self._crumb
        try:
            self.session.get("https://finance.yahoo.com/", timeout=10)
            res = self.session.get(
                "https://query1.finance.yahoo.com/v1/test/getcrumb", timeout=10
            )
            if res.status_code == 200:
                self._crumb = res.text
            return self._crumb or ""
        except Exception:
            return ""

    def get_stock_data(self, ticker: str, range_key: str = "1y") -> pd.DataFrame:
        start_time = time.time()
        cache_key = f"{ticker}_{range_key}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            self.last_latency = (time.time() - start_time) * 1000
            return cached

        period = self.RANGE_MAP.get(range_key, "1y")
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range={period}&interval=1d"
            response = self.session.get(url, timeout=10)
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
                "previousClose": meta.get("previousClose")
                or meta.get("chartPreviousClose"),
                "fiftyTwoWeekHigh": meta.get("fiftyTwoWeekHigh"),
                "fiftyTwoWeekLow": meta.get("fiftyTwoWeekLow"),
                "currency": meta.get("currency"),
                "exchangeName": meta.get("exchangeName"),
                "regularMarketPrice": meta.get("regularMarketPrice"),
            }

            df = df.dropna(subset=["Open", "High", "Low", "Close"], how="all")
            if not df.empty and pd.isna(df["Close"].iloc[-1]):
                df = df.iloc[:-1]

            if df.empty:
                raise ValueError(f"No data found for ticker: {ticker}")

            self.cache.set(cache_key, df)
            self.last_latency = (time.time() - start_time) * 1000
            return df

        except Exception as e:
            self.last_latency = (time.time() - start_time) * 1000
            raise ValueError(f"Error fetching data for {ticker}: {str(e)}") from e

    def get_company_info(self, ticker: str) -> dict[str, Any]:
        start_time = time.time()
        cache_key = f"{ticker}_info"
        cached = self.cache.get(cache_key)
        if cached is not None:
            self.last_latency = (time.time() - start_time) * 1000
            return cached

        info = {}

        # 1. Fetch Sector/Industry from Search API
        try:
            url_search = (
                f"https://query2.finance.yahoo.com/v1/finance/search?q={ticker}"
            )
            response_search = self.session.get(url_search, timeout=10)
            if response_search.status_code == 200:
                data_search = response_search.json()
                if data_search.get("quotes"):
                    quote_s = data_search["quotes"][0]
                    info.update(
                        {
                            "sector": quote_s.get("sector"),
                            "industry": quote_s.get("industry"),
                            "exchange": quote_s.get("exchange"),
                            "type": quote_s.get("quoteType"),
                        }
                    )
        except Exception:
            pass

        # 2. Fetch Market Cap from Quote API (requires crumb)
        try:
            crumb = self._get_crumb()
            if crumb:
                url_quote = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={ticker}&crumb={crumb}"
                response_quote = self.session.get(url_quote, timeout=10)
                if response_quote.status_code == 200:
                    data_quote = response_quote.json()
                    if data_quote.get("quoteResponse", {}).get("result"):
                        quote_q = data_quote["quoteResponse"]["result"][0]
                        info["marketCap"] = quote_q.get("marketCap")
                        info["previousClose"] = quote_q.get(
                            "regularMarketPreviousClose"
                        )
        except Exception:
            pass

        self.cache.set(cache_key, info)
        self.last_latency = (time.time() - start_time) * 1000
        return info

    def validate_ticker(self, ticker: str) -> bool:
        try:
            df = self.get_stock_data(ticker, "1m")
            return not df.empty
        except Exception:
            return False
