"""Unified metadata service with provider priority and caching.

Provider priority (highest first):
  1. Finnhub (NSE: format for Indian stocks)
  2. Yahoo Finance (t.info / fast_info)
  3. Screener.in (Indian stock profiles)
  4. Computed (sharesOutstanding x currentPrice)
  5. Cached (previous successful fetch, within 24h)
  6. Not Available
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from services.finnhub_service import finnhub_service
from services.screener_provider import fetch_company_profile
from services.symbol_converter import is_indian_ticker

logger = logging.getLogger("stock_dashboard")

_CACHE_TTL = 24 * 60 * 60  # 24 hours


@dataclass
class ProviderResult:
    sector: str | None = None
    industry: str | None = None
    country: str | None = None
    market_cap: float | None = None
    name: str | None = None
    source: str | None = None
    is_computed: bool = False


@dataclass
class ProviderDiagnostic:
    provider: str
    status: str  # "success" | "empty" | "error" | "skipped"
    fields_returned: list[str] = field(default_factory=list)
    reason: str | None = None
    latency_ms: float = 0.0


class MetadataService:
    def __init__(self) -> None:
        self._cache: dict[str, tuple[float, ProviderResult]] = {}
        self._ttls: dict[str, float] = {}
        self.last_diagnostics: list[ProviderDiagnostic] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_company_metadata(
        self,
        ticker: str,
        yahoo_info: dict[str, Any] | None = None,
    ) -> ProviderResult:
        """Fetch company metadata through the provider fallback chain.

        Parameters
        ----------
        ticker : str  (e.g. "RELIANCE.NS", "AAPL")
        yahoo_info : dict | None
            Pre-fetched yahoo info (from get_company_info) to avoid
            redundant calls.

        Returns
        -------
        ProviderResult with the best available data.
        """
        self.last_diagnostics = []
        cache_key = ticker.upper()

        # 1. Check cache
        cached = self._cache.get(cache_key)
        if cached:
            ts, cached_result = cached
            ttl = self._ttls.get(cache_key, _CACHE_TTL)
            if time.time() - ts < ttl:
                self.last_diagnostics.append(
                    ProviderDiagnostic(
                        provider="cache", status="success",
                        fields_returned=self._filled_fields(cached_result),
                    )
                )
                return cached_result

        result = ProviderResult()

        # 2. Finnhub
        result = await self._try_finnhub(ticker, result)

        # 3. Yahoo Finance
        result = self._try_yahoo(ticker, yahoo_info, result)

        # 4. Screener.in (Indian stocks only)
        if is_indian_ticker(ticker):
            result = await self._try_screener(ticker, result)

        # 5. Computed market cap
        result = self._try_computed(ticker, yahoo_info, result)

        # 6. Cache and return
        self._cache[cache_key] = (time.time(), result)
        has_data = bool(
            result.sector or result.industry or result.country or result.market_cap
        )
        self._ttls[cache_key] = _CACHE_TTL if has_data else 60

        logger.info(
            "Metadata final for %s: sector=%s industry=%s market_cap=%s source=%s",
            ticker, result.sector, result.industry, result.market_cap, result.source,
        )
        return result

    # ------------------------------------------------------------------
    # Sanitization helpers
    # ------------------------------------------------------------------

    def _clean_text(self, val: Any) -> str | None:
        if val is None:
            return None
        text = str(val).strip()
        if text and text.lower() not in {"n/a", "na", "none", "null", "-", "not available"}:
            return text
        return None

    def _clean_number(self, val: Any) -> float | None:
        if val is None:
            return None
        try:
            number = float(val)
            # market cap and share numbers are always > 0. Check number != number for NaN.
            if number == number and number > 0:
                return number
        except (TypeError, ValueError):
            pass
        return None

    # ------------------------------------------------------------------
    # Provider steps
    # ------------------------------------------------------------------

    async def _try_finnhub(
        self, ticker: str, current: ProviderResult,
    ) -> ProviderResult:
        start = time.time()
        diag = ProviderDiagnostic(provider="finnhub", status="skipped")

        try:
            profile = await finnhub_service.get_company_profile(ticker)
            if profile:
                sector = self._clean_text(profile.get("sector"))
                industry = self._clean_text(profile.get("finnhubIndustry"))
                country = self._clean_text(profile.get("country"))
                mc = self._clean_number(profile.get("marketCapitalization"))
                name = self._clean_text(profile.get("name"))

                if sector or industry or country or mc:
                    current.sector = current.sector or sector
                    current.industry = current.industry or industry
                    current.country = current.country or country
                    if mc:
                        current.market_cap = current.market_cap or (mc * 1_000_000)
                    current.name = current.name or name
                    current.source = "finnhub"
                    diag.status = "success"
                    diag.fields_returned = self._filled_fields(current)
                else:
                    diag.status = "empty"
                    diag.reason = "profile returned no sector/industry/marketCap"
            else:
                diag.status = "empty"
                diag.reason = "no profile returned"
        except Exception as exc:
            diag.status = "error"
            diag.reason = str(exc)

        diag.latency_ms = (time.time() - start) * 1000
        self.last_diagnostics.append(diag)
        return current

    def _try_yahoo(
        self, ticker: str, yahoo_info: dict[str, Any] | None,
        current: ProviderResult,
    ) -> ProviderResult:
        start = time.time()
        diag = ProviderDiagnostic(provider="yahoo", status="skipped")

        if yahoo_info:
            sector = self._clean_text(yahoo_info.get("sector"))
            industry = self._clean_text(yahoo_info.get("industry"))
            country = self._clean_text(yahoo_info.get("country"))
            mc = self._clean_number(yahoo_info.get("marketCap"))
            name = self._clean_text(yahoo_info.get("longName") or yahoo_info.get("shortName"))

            if sector or industry or country or mc or name:
                current.sector = current.sector or sector
                current.industry = current.industry or industry
                current.country = current.country or country
                current.market_cap = current.market_cap or mc
                current.name = current.name or name
                if not current.source and (sector or industry or mc):
                    current.source = "yahoo"
                diag.status = "success"
                diag.fields_returned = self._filled_fields(current)
            else:
                diag.status = "empty"
                diag.reason = "yahoo_info had no sector/industry/marketCap"
        else:
            diag.status = "skipped"
            diag.reason = "yahoo_info not provided"

        diag.latency_ms = (time.time() - start) * 1000
        self.last_diagnostics.append(diag)
        return current

    async def _try_screener(
        self, ticker: str, current: ProviderResult,
    ) -> ProviderResult:
        start = time.time()
        diag = ProviderDiagnostic(provider="screener.in", status="skipped")

        try:
            profile = fetch_company_profile(ticker)
            if profile:
                sector = self._clean_text(profile.get("sector"))
                industry = self._clean_text(profile.get("industry"))
                mc = self._clean_number(profile.get("marketCap"))
                name = self._clean_text(profile.get("name"))

                if sector or industry or mc:
                    current.sector = current.sector or sector
                    current.industry = current.industry or industry
                    current.market_cap = current.market_cap or mc
                    current.name = current.name or name
                    current.source = "screener.in"
                    diag.status = "success"
                    diag.fields_returned = self._filled_fields(current)
                else:
                    diag.status = "empty"
                    diag.reason = "no useful fields returned"
            else:
                diag.status = "empty"
                diag.reason = "no profile returned"
        except Exception as exc:
            diag.status = "error"
            diag.reason = str(exc)

        diag.latency_ms = (time.time() - start) * 1000
        self.last_diagnostics.append(diag)
        return current

    def _try_computed(
        self, ticker: str, yahoo_info: dict[str, Any] | None,
        current: ProviderResult,
    ) -> ProviderResult:
        start = time.time()
        diag = ProviderDiagnostic(provider="computed", status="skipped")

        if not current.market_cap and yahoo_info:
            shares = self._clean_number(yahoo_info.get("sharesOutstanding") or yahoo_info.get("impliedSharesOutstanding"))
            price = self._clean_number(yahoo_info.get("regularMarketPrice") or yahoo_info.get("currentPrice"))
            if shares and price:
                current.market_cap = shares * price
                current.source = "computed"
                diag.status = "success"
                diag.fields_returned = ["marketCap"]
                logger.info(
                    "Computed market cap for %s: shares=%s * price=%s = %s",
                    ticker, shares, price, current.market_cap,
                )
            else:
                diag.status = "skipped"
                diag.reason = f"missing shares({shares}) or price({price})"

        diag.latency_ms = (time.time() - start) * 1000
        self.last_diagnostics.append(diag)
        return current

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _filled_fields(result: ProviderResult) -> list[str]:
        fields = []
        if result.sector:
            fields.append("sector")
        if result.industry:
            fields.append("industry")
        if result.country:
            fields.append("country")
        if result.market_cap:
            fields.append("marketCap")
        if result.name:
            fields.append("name")
        return fields


metadata_service = MetadataService()

