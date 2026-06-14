import logging
import time
from typing import Any, cast
import pandas as pd
import yfinance as yf
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
        self.cache_ttl = 300  # Default fallback cache TTL
        import requests
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        })

    def _get_ticker(self, ticker: str) -> yf.Ticker:
        return yf.Ticker(ticker, session=self.session)

    def _get_current_ttl(self) -> int:
        try:
            now_ny = pd.Timestamp.now(tz="America/New_York")
            is_weekend = now_ny.weekday() >= 5
            is_market_hours = not is_weekend and (
                (now_ny.hour == 9 and now_ny.minute >= 30) or
                (10 <= now_ny.hour < 16)
            )
            return 60 if is_market_hours else 300
        except Exception as e:
            logger.warning(f"Error determining market hours: {e}")
            return 60

    def _get_with_retry(self, func, max_retries=5, initial_delay=1.0, backoff_factor=2.0):
        delay = initial_delay
        last_exception = None
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                time.sleep(delay)
                delay *= backoff_factor
        raise last_exception

    def get_stock_data(self, ticker: str, range_key: str = "1y", force_refresh: bool = False) -> pd.DataFrame:
        start_time = time.time()
        cache_key = f"{ticker}_{range_key}_df"
        ttl = self._get_current_ttl()
        
        cached_tuple = self.cache.get(cache_key)
        if not force_refresh and cached_tuple is not None and isinstance(cached_tuple, tuple):
            cached_time, cached_df = cached_tuple
            if time.time() - cached_time < ttl:
                self.last_latency = (time.time() - start_time) * 1000
                return cached_df

        period = self.RANGE_MAP.get(range_key, "1y")
        try:
            def _fetch_history():
                t = self._get_ticker(ticker)
                return t.history(period=period, interval="1d")
                
            df = self._get_with_retry(_fetch_history)

            if df.empty:
                raise ValueError(f"No results found for ticker: {ticker}")

            # Ensure index is datetime
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)
            
            # Ensure index is timezone-aware
            if df.index.tz is None:
                tz_name = "UTC"
                try:
                    t = self._get_ticker(ticker)
                    if hasattr(t, "fast_info") and "timezone" in t.fast_info:
                        tz_name = t.fast_info["timezone"]
                except Exception:
                    pass
                df.index = df.index.tz_localize(tz_name)
                
            df.index.name = "Date"
            
            # Fetch metadata using fast_info first, falling back to info
            meta = {}
            try:
                def _fetch_meta():
                    t = self._get_ticker(ticker)
                    fast_info = t.fast_info
                    
                    def get_fast_val(key, attr):
                        try:
                            val = fast_info[key]
                            if val is not None and not (isinstance(val, float) and pd.isna(val)):
                                return val
                        except Exception:
                            pass
                        try:
                            val = getattr(fast_info, attr)
                            if val is not None and not (isinstance(val, float) and pd.isna(val)):
                                return val
                        except Exception:
                            pass
                        return None

                    pc = get_fast_val("previous_close", "previous_close")
                    h52 = get_fast_val("year_high", "year_high")
                    l52 = get_fast_val("year_low", "year_low")
                    curr = get_fast_val("currency", "currency")
                    exch = get_fast_val("exchange", "exchange")
                    lp = get_fast_val("last_price", "last_price")
                    
                    full_info = {}
                    if pc is None or h52 is None or l52 is None or curr is None or exch is None or lp is None:
                        try:
                            full_info = t.info
                        except Exception as e:
                            logger.warning(f"Metadata fallback t.info failed: {e}")
                            
                    return {
                        "regularMarketPrice": lp if lp is not None else (full_info.get("regularMarketPrice") or full_info.get("currentPrice")),
                        "currency": curr if curr is not None else full_info.get("currency"),
                        "previousClose": pc if pc is not None else full_info.get("previousClose"),
                        "fiftyTwoWeekHigh": h52 if h52 is not None else full_info.get("fiftyTwoWeekHigh"),
                        "fiftyTwoWeekLow": l52 if l52 is not None else full_info.get("fiftyTwoWeekLow"),
                        "exchangeName": exch if exch is not None else full_info.get("exchange"),
                    }
                
                meta = self._get_with_retry(_fetch_meta)
            except Exception as e:
                logger.warning(f"Error fetching metadata for {ticker}: {e}")

            df.attrs["metadata"] = meta
            
            # Avoid dropping the latest candle if some fields are NaN (like Volume, etc.)
            df = df.dropna(subset=["Open", "High", "Low", "Close"])
            
            if df.empty:
                raise ValueError(f"No valid data points for ticker: {ticker}")

            self.cache.set(cache_key, (time.time(), df))
            self.last_latency = (time.time() - start_time) * 1000
            return df

        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {str(e)}")
            raise ValueError(f"Error fetching data for {ticker}: {str(e)}") from e

    def get_company_info(self, ticker: str) -> dict[str, Any]:
        start_time = time.time()
        cache_key = f"{ticker}_info_dict"
        ttl = self._get_current_ttl()
        
        cached_tuple = self.cache.get(cache_key)
        if cached_tuple is not None and isinstance(cached_tuple, tuple):
            cached_time, cached_info = cached_tuple
            if time.time() - cached_time < ttl:
                self.last_latency = (time.time() - start_time) * 1000
                return cast(dict[str, Any], cached_info)

        info: dict[str, Any] = {}
        try:
            def _fetch_ticker_info():
                t = self._get_ticker(ticker)
                fast_info = t.fast_info
                
                def get_fast_val(key, attr):
                    try:
                        val = fast_info[key]
                        if val is not None and not (isinstance(val, float) and pd.isna(val)):
                            return val
                    except Exception:
                        pass
                    try:
                        val = getattr(fast_info, attr)
                        if val is not None and not (isinstance(val, float) and pd.isna(val)):
                            return val
                    except Exception:
                        pass
                    return None

                pc = get_fast_val("previous_close", "previous_close")
                h52 = get_fast_val("year_high", "year_high")
                l52 = get_fast_val("year_low", "year_low")
                mc = get_fast_val("market_cap", "market_cap")
                curr = get_fast_val("currency", "currency")
                exch = get_fast_val("exchange", "exchange")
                lp = get_fast_val("last_price", "last_price")

                # Fetch t.info only if required (for sector, industry, longName, and fallback for others)
                full_info = {}
                try:
                    full_info = t.info
                except Exception as info_err:
                    logger.warning(f"Failed to fetch t.info for {ticker}: {info_err}")

                return {
                    "sector": full_info.get("sector"),
                    "industry": full_info.get("industry"),
                    "marketCap": mc if mc is not None else (full_info.get("marketCap") or (full_info.get("marketCapitalization", 0) * 1000000 if full_info.get("marketCapitalization") else None)),
                    "previousClose": pc if pc is not None else full_info.get("previousClose"),
                    "longName": full_info.get("longName") or full_info.get("shortName"),
                    "fiftyTwoWeekHigh": h52 if h52 is not None else full_info.get("fiftyTwoWeekHigh"),
                    "fiftyTwoWeekLow": l52 if l52 is not None else full_info.get("fiftyTwoWeekLow"),
                    "currency": curr if curr is not None else full_info.get("currency"),
                    "exchange": exch if exch is not None else full_info.get("exchange"),
                    "regularMarketPrice": lp if lp is not None else (full_info.get("regularMarketPrice") or full_info.get("currentPrice")),
                }

            info = self._get_with_retry(_fetch_ticker_info)
        except Exception as e:
            logger.warning(f"Error fetching info for {ticker}: {e}")

        self.cache.set(cache_key, (time.time(), info))
        self.last_latency = (time.time() - start_time) * 1000
        return info

