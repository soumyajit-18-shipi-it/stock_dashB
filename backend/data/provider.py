import logging
import time
from typing import Any, cast, Callable, Dict, Optional
import pandas as pd
import yfinance as yf
from data.cache import DataCache

logger = logging.getLogger("stock_dashboard")


def sanitize_value(val: Any) -> Any:
    """Ensure val is a JSON-serializable Python float, int, str, or None, filtering NaNs."""
    if val is None:
        return None
    # Check for pandas/numpy NaN
    if isinstance(val, float) and pd.isna(val):
        return None
    # Convert numpy types to native Python types
    if hasattr(val, "item"):
        try:
            val = val.item()
        except Exception:
            pass
    if isinstance(val, float) and pd.isna(val):
        return None

    return val


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
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            }
        )

    def _get_ticker(self, ticker: str) -> yf.Ticker:
        return yf.Ticker(ticker, session=self.session)

    def _get_current_ttl(self, ticker: str = "") -> int:
        try:
            upper = ticker.strip().upper()
            if upper.endswith(".NS") or upper.endswith(".BO"):
                # NSE/BSE trading hours: 09:15-15:30 IST (UTC+5:30)
                now_exchange = pd.Timestamp.now(tz="Asia/Kolkata")
                is_weekend = now_exchange.weekday() >= 5
                is_market_hours = not is_weekend and (
                    (now_exchange.hour == 9 and now_exchange.minute >= 15)
                    or (10 <= now_exchange.hour < 15)
                    or (now_exchange.hour == 15 and now_exchange.minute <= 30)
                )
                return 60 if is_market_hours else 300

            # Default: NYSE/NASDAQ trading hours: 09:30-16:00 ET
            now_exchange = pd.Timestamp.now(tz="America/New_York")
            is_weekend = now_exchange.weekday() >= 5
            is_market_hours = not is_weekend and (
                (now_exchange.hour == 9 and now_exchange.minute >= 30)
                or (10 <= now_exchange.hour < 16)
            )
            return 60 if is_market_hours else 300
        except Exception as e:
            logger.warning(f"Error determining market hours: {e}")
            return 60

    def _get_with_retry(
        self,
        func: Callable[[], Any],
        max_retries: int = 2,
        initial_delay: float = 0.1,
        backoff_factor: float = 1.5,
    ) -> Any:
        delay = initial_delay
        last_exception: Optional[Exception] = None
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s..."
                )
                time.sleep(delay)
                delay *= backoff_factor
        if last_exception is not None:
            raise last_exception
        raise Exception("Retry failed without an exception")

    def _fetch_stock_data_direct(self, ticker: str, range_key: str) -> pd.DataFrame:
        """Fallback to fetch chart/candle data directly from Yahoo Finance API via requests."""
        period = self.RANGE_MAP.get(range_key, "1y")
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range={period}&interval=1d"
        logger.info(f"Attempting direct HTTP fetch from: {url}")

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

        opens = indicators.get("open") or []
        highs = indicators.get("high") or []
        lows = indicators.get("low") or []
        closes = indicators.get("close") or []
        volumes = indicators.get("volume") or []

        if not opens:
            raise ValueError(f"No price candles found for ticker: {ticker}")

        df = pd.DataFrame(
            {
                "Open": opens,
                "High": highs,
                "Low": lows,
                "Close": closes,
                "Volume": volumes,
            },
            index=pd.to_datetime(timestamps, unit="s"),
        )

        # Determine exchange timezone name
        tz_name = meta.get("exchangeTimezoneName") or "UTC"
        try:
            df.index = df.index.tz_localize("UTC").tz_convert(tz_name)
        except Exception:
            try:
                df.index = df.index.tz_localize(tz_name)
            except Exception:
                if df.index.tz is None:
                    df.index = df.index.tz_localize("UTC")

        df.index.name = "Date"
        df.attrs["metadata"] = {
            "regularMarketPrice": sanitize_value(meta.get("regularMarketPrice")),
            "currency": sanitize_value(meta.get("currency") or ("INR" if ticker.upper().endswith(".NS") or ticker.upper().endswith(".BO") else "USD")),
            "previousClose": sanitize_value(
                meta.get("previousClose") or meta.get("chartPreviousClose")
            ),
            "fiftyTwoWeekHigh": sanitize_value(meta.get("fiftyTwoWeekHigh")),
            "fiftyTwoWeekLow": sanitize_value(meta.get("fiftyTwoWeekLow")),
            "exchangeName": sanitize_value(meta.get("exchangeName")),
            "longName": sanitize_value(meta.get("longName") or meta.get("shortName")),
        }

        # Keep only the rows with valid core price candles
        df = df.dropna(subset=["Open", "High", "Low", "Close"])

        if df.empty:
            raise ValueError(f"No valid data points for ticker: {ticker}")

        return df

    def _fetch_company_info_direct(self, ticker: str) -> dict[str, Any]:
        """Fallback to fetch company quote summary directly from Yahoo Finance API via requests."""
        url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={ticker}"
        logger.info(f"Attempting direct HTTP quote fetch from: {url}")

        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get("quoteResponse", {}).get("result"):
            raise ValueError(f"No quote results found for ticker: {ticker}")

        quote = data["quoteResponse"]["result"][0]

        return {
            "sector": sanitize_value(quote.get("sector")),
            "industry": sanitize_value(quote.get("industry")),
            "marketCap": sanitize_value(quote.get("marketCap")),
            "previousClose": sanitize_value(quote.get("regularMarketPreviousClose")),
            "longName": sanitize_value(quote.get("longName") or quote.get("shortName")),
            "fiftyTwoWeekHigh": sanitize_value(quote.get("fiftyTwoWeekHigh")),
            "fiftyTwoWeekLow": sanitize_value(quote.get("fiftyTwoWeekLow")),
            "currency": sanitize_value(quote.get("currency")),
            "exchange": sanitize_value(quote.get("exchange")),
            "regularMarketPrice": sanitize_value(quote.get("regularMarketPrice")),
            "country": sanitize_value(quote.get("market")),
            "website": None,
            "logo": None,
        }

    def get_stock_data(
        self, ticker: str, range_key: str = "1y", force_refresh: bool = False
    ) -> pd.DataFrame:
        start_time = time.time()
        cache_key = f"{ticker}_{range_key}_df"
        ttl = self._get_current_ttl(ticker)

        cached_tuple = self.cache.get(cache_key)
        if (
            not force_refresh
            and cached_tuple is not None
            and isinstance(cached_tuple, tuple)
        ):
            cached_time, cached_df = cached_tuple
            if time.time() - cached_time < ttl:
                self.last_latency = (time.time() - start_time) * 1000
                return cached_df

        period = self.RANGE_MAP.get(range_key, "1y")
        try:
            logger.info(f"Attempting to fetch history for {ticker} using yfinance...")

            def _fetch_history() -> pd.DataFrame:
                t = self._get_ticker(ticker)
                return cast(pd.DataFrame, t.history(period=period, interval="1d"))

            df = cast(pd.DataFrame, self._get_with_retry(_fetch_history))

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

                def _fetch_meta() -> Dict[str, Any]:
                    t = self._get_ticker(ticker)
                    fast_info = t.fast_info

                    def get_fast_val(key: str, attr: str) -> Any:
                        try:
                            val = fast_info[key]
                            if val is not None and not (
                                isinstance(val, float) and pd.isna(val)
                            ):
                                return val
                        except Exception:
                            pass
                        try:
                            val = getattr(fast_info, attr)
                            if val is not None and not (
                                isinstance(val, float) and pd.isna(val)
                            ):
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
                    if (
                        pc is None
                        or h52 is None
                        or l52 is None
                        or curr is None
                        or exch is None
                        or lp is None
                    ):
                        try:
                            full_info = t.info
                        except Exception as e:
                            logger.warning(f"Metadata fallback t.info failed: {e}")

                    return {
                        "regularMarketPrice": sanitize_value(
                            lp
                            if lp is not None
                            else (
                                full_info.get("regularMarketPrice")
                                or full_info.get("currentPrice")
                            )
                        ),
                        "currency": sanitize_value(
                            curr if curr is not None else full_info.get("currency")
                        ),
                        "previousClose": sanitize_value(
                            pc if pc is not None else full_info.get("previousClose")
                        ),
                        "fiftyTwoWeekHigh": sanitize_value(
                            h52
                            if h52 is not None
                            else full_info.get("fiftyTwoWeekHigh")
                        ),
                        "fiftyTwoWeekLow": sanitize_value(
                            l52 if l52 is not None else full_info.get("fiftyTwoWeekLow")
                        ),
                        "exchangeName": sanitize_value(
                            exch if exch is not None else full_info.get("exchange")
                        ),
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
            logger.warning(
                f"yfinance failed to fetch stock data for {ticker}: {e}. Falling back to direct API..."
            )
            try:
                df = self._fetch_stock_data_direct(ticker, range_key)
                self.cache.set(cache_key, (time.time(), df))
                self.last_latency = (time.time() - start_time) * 1000
                return df
            except Exception as direct_err:
                logger.error(
                    f"Both yfinance and direct API failed for {ticker}. Direct API error: {direct_err}"
                )
                raise ValueError(
                    f"Error fetching data for {ticker}: {str(direct_err)}"
                ) from direct_err

    def get_company_info(self, ticker: str) -> dict[str, Any]:
        start_time = time.time()
        cache_key = f"{ticker}_info_dict"
        ttl = 12 * 60 * 60

        cached_tuple = self.cache.get(cache_key)
        if cached_tuple is not None and isinstance(cached_tuple, tuple):
            cached_time, cached_info = cached_tuple
            if time.time() - cached_time < ttl:
                self.last_latency = (time.time() - start_time) * 1000
                return cast(dict[str, Any], cached_info)

        info: dict[str, Any] = {}
        try:
            logger.info(
                f"Attempting to fetch company info for {ticker} using yfinance..."
            )

            def _get_fast_info_vals() -> Dict[str, Any]:
                """Extract available fields from t.fast_info (reliable)."""
                t = self._get_ticker(ticker)
                fi = t.fast_info

                def get_val(key: str, attr: str) -> Any:
                    for source in [lambda k: fi[k], lambda k: getattr(fi, k)]:
                        try:
                            val = source(attr)
                            if val is not None and not (
                                isinstance(val, float) and pd.isna(val)
                            ):
                                return val
                        except Exception:
                            pass
                    return None

                return {
                    "previousClose": sanitize_value(get_val("previous_close", "previous_close")),
                    "fiftyTwoWeekHigh": sanitize_value(get_val("year_high", "year_high")),
                    "fiftyTwoWeekLow": sanitize_value(get_val("year_low", "year_low")),
                    "marketCap": sanitize_value(get_val("market_cap", "market_cap")),
                    "currency": sanitize_value(get_val("currency", "currency")),
                    "exchange": sanitize_value(get_val("exchange", "exchange")),
                    "regularMarketPrice": sanitize_value(get_val("last_price", "last_price")),
                }

            def _get_t_info() -> Dict[str, Any]:
                """Fetch t.info (may be rate-limited)."""
                t = self._get_ticker(ticker)
                try:
                    raw = t.info
                    return {
                        "sector": sanitize_value(raw.get("sector")),
                        "industry": sanitize_value(raw.get("industry")),
                        "marketCap": sanitize_value(
                            raw.get("marketCap")
                            or (
                                raw.get("marketCapitalization", 0) * 1000000
                                if raw.get("marketCapitalization")
                                else None
                            )
                        ),
                        "previousClose": sanitize_value(raw.get("previousClose")),
                        "longName": sanitize_value(raw.get("longName") or raw.get("shortName")),
                        "fiftyTwoWeekHigh": sanitize_value(raw.get("fiftyTwoWeekHigh")),
                        "fiftyTwoWeekLow": sanitize_value(raw.get("fiftyTwoWeekLow")),
                        "currency": sanitize_value(raw.get("currency")),
                        "exchange": sanitize_value(raw.get("exchange")),
                        "regularMarketPrice": sanitize_value(
                            raw.get("regularMarketPrice") or raw.get("currentPrice")
                        ),
                        "country": sanitize_value(raw.get("country")),
                        "website": sanitize_value(raw.get("website")),
                        "logo": sanitize_value(raw.get("logo_url") or raw.get("logo")),
                        "sharesOutstanding": sanitize_value(raw.get("sharesOutstanding")),
                        "impliedSharesOutstanding": sanitize_value(raw.get("impliedSharesOutstanding")),
                        "revenueGrowth": sanitize_value(raw.get("revenueGrowth")),
                        "earningsGrowth": sanitize_value(
                            raw.get("earningsGrowth") or raw.get("earningsQuarterlyGrowth")
                        ),
                        "debtToEquity": sanitize_value(raw.get("debtToEquity")),
                        "returnOnEquity": sanitize_value(raw.get("returnOnEquity")),
                        "returnOnAssets": sanitize_value(raw.get("returnOnAssets")),
                        "currentRatio": sanitize_value(raw.get("currentRatio")),
                        "quickRatio": sanitize_value(raw.get("quickRatio")),
                        "operatingMargins": sanitize_value(raw.get("operatingMargins")),
                        "profitMargins": sanitize_value(raw.get("profitMargins")),
                        "freeCashflow": sanitize_value(raw.get("freeCashflow")),
                        "operatingCashflow": sanitize_value(raw.get("operatingCashflow")),
                        "enterpriseValue": sanitize_value(raw.get("enterpriseValue")),
                        "trailingPegRatio": sanitize_value(
                            raw.get("trailingPegRatio") or raw.get("pegRatio")
                        ),
                        "trailingPE": sanitize_value(raw.get("trailingPE")),
                        "forwardPE": sanitize_value(raw.get("forwardPE")),
                        "priceToBook": sanitize_value(raw.get("priceToBook")),
                        "dividendYield": sanitize_value(raw.get("dividendYield")),
                        "heldPercentInstitutions": sanitize_value(
                            raw.get("heldPercentInstitutions")
                        ),
                        "heldPercentInsiders": sanitize_value(
                            raw.get("heldPercentInsiders")
                        ),
                    }
                except Exception as e:
                    logger.warning(f"t.info failed for {ticker}: {e}")
                    return {}

            # Step 1: fetch fast_info (reliable, rarely fails)
            fast = _get_fast_info_vals()
            info.update(fast)
            logger.info(
                "fast_info for %s: marketCap=%s currency=%s exchange=%s price=%s",
                ticker, info.get("marketCap"), info.get("currency"),
                info.get("exchange"), info.get("regularMarketPrice"),
            )

            # Step 2: try t.info with longer delays (may be rate-limited)
            t_info_result = self._get_with_retry(
                _get_t_info, max_retries=3, initial_delay=2.0, backoff_factor=3.0
            )
            info.update({k: v for k, v in t_info_result.items() if v is not None})
            logger.info(
                "t.info result for %s: sector=%s industry=%s longName=%s marketCap=%s",
                ticker,
                info.get("sector"), info.get("industry"),
                info.get("longName"), info.get("marketCap"),
            )

            info = {k: sanitize_value(v) for k, v in info.items()}
        except Exception as e:
            logger.warning(
                f"yfinance failed to fetch company info for {ticker}: {e}. Falling back to direct API..."
            )
            try:
                info = self._fetch_company_info_direct(ticker)
            except Exception as direct_err:
                logger.error(
                    f"Both yfinance and direct API failed to fetch company info for {ticker}. Direct API error: {direct_err}"
                )

        self.cache.set(cache_key, (time.time(), info))
        self.last_latency = (time.time() - start_time) * 1000
        logger.info(
            "Final company info for %s: keys=%s sector=%s industry=%s marketCap=%s longName=%s",
            ticker, list(info.keys()),
            info.get("sector"), info.get("industry"),
            info.get("marketCap"), info.get("longName"),
        )
        return info
