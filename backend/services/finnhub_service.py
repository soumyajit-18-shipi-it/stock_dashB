"""Async Finnhub adapter with endpoint-specific caches and graceful failures."""

from __future__ import annotations

import json
import logging
import time
from datetime import date, timedelta
from typing import Any, cast

import httpx

from core.config import settings
from services.symbol_converter import to_finnhub_symbol

logger = logging.getLogger("stock_dashboard")


class FinnhubService:
    BASE_URL = "https://finnhub.io/api/v1"

    def __init__(self) -> None:
        self.api_key = settings.FINNHUB_API_KEY
        self.last_latency = 0.0
        self._profile_cache: dict[str, tuple[float, dict[str, Any] | None]] = {}
        self._financial_cache: dict[str, tuple[float, dict[str, Any]]] = {}
        self._news_cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}
        self.profile_ttl = 12 * 60 * 60
        self.financial_ttl = 12 * 60 * 60
        self.news_ttl = 15 * 60

    async def get_company_profile(self, ticker: str) -> dict[str, Any] | None:
        if not self.api_key:
            logger.warning(
                "Finnhub API key not configured; skipping profile fetch for %s",
                ticker,
            )
            return None

        start_time = time.time()
        original_symbol = ticker.upper()
        cached = self._profile_cache.get(original_symbol)
        if cached and time.time() - cached[0] < self.profile_ttl:
            self.last_latency = (time.time() - start_time) * 1000
            return cached[1]

        finnhub_symbol = to_finnhub_symbol(original_symbol)
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(5.0, connect=2.0)
            ) as client:
                response = await client.get(
                    f"{self.BASE_URL}/stock/profile2",
                    params={"symbol": finnhub_symbol, "token": self.api_key},
                )
                self.last_latency = (time.time() - start_time) * 1000
                if response.status_code != 200:
                    logger.warning(
                        "Finnhub profile returned %d for %s: %s",
                        response.status_code,
                        original_symbol,
                        response.text[:200],
                    )
                    return None
                data = cast(dict[str, Any], response.json())
                logger.debug(
                    "Finnhub profile response for %s: %s",
                    original_symbol,
                    json.dumps(data, default=str)[:500],
                )
                self._profile_cache[original_symbol] = (time.time(), data)
                return data
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self.last_latency = (time.time() - start_time) * 1000
            logger.warning("Finnhub profile fetch failed for %s: %s", ticker, exc)
            return None

    async def get_basic_financials(self, ticker: str) -> dict[str, Any]:
        """Return Finnhub's standardized basic financial metrics."""
        if not self.api_key:
            return {}
        symbol = to_finnhub_symbol(ticker.upper())
        cached = self._financial_cache.get(symbol)
        if cached and time.time() - cached[0] < self.financial_ttl:
            return cached[1]
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(8.0, connect=3.0)
            ) as client:
                response = await client.get(
                    f"{self.BASE_URL}/stock/metric",
                    params={
                        "symbol": symbol,
                        "metric": "all",
                        "token": self.api_key,
                    },
                )
                response.raise_for_status()
                payload = cast(dict[str, Any], response.json())
                metrics = cast(dict[str, Any], payload.get("metric") or {})
                self._financial_cache[symbol] = (time.time(), metrics)
                return metrics
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.warning("Finnhub financial metrics failed for %s: %s", ticker, exc)
            return {}

    async def get_company_news(
        self, ticker: str, lookback_days: int = 30
    ) -> list[dict[str, Any]]:
        """Return recent company news, cached independently from profiles."""
        if not self.api_key:
            return []
        symbol = to_finnhub_symbol(ticker.upper())
        cache_key = f"{symbol}:{lookback_days}"
        cached = self._news_cache.get(cache_key)
        if cached and time.time() - cached[0] < self.news_ttl:
            return cached[1]

        end = date.today()
        start = end - timedelta(days=max(1, lookback_days))
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(8.0, connect=3.0)
            ) as client:
                response = await client.get(
                    f"{self.BASE_URL}/company-news",
                    params={
                        "symbol": symbol,
                        "from": start.isoformat(),
                        "to": end.isoformat(),
                        "token": self.api_key,
                    },
                )
                response.raise_for_status()
                payload = response.json()
                news = payload if isinstance(payload, list) else []
                normalized = [
                    cast(dict[str, Any], item)
                    for item in news
                    if isinstance(item, dict) and item.get("headline")
                ]
                self._news_cache[cache_key] = (time.time(), normalized)
                return normalized
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.warning("Finnhub company news failed for %s: %s", ticker, exc)
            return []


finnhub_service = FinnhubService()
