import json
import time
from typing import Any, cast

import httpx
from core.config import settings
from services.symbol_converter import to_finnhub_symbol

import logging
logger = logging.getLogger("stock_dashboard")


class FinnhubService:
    BASE_URL = "https://finnhub.io/api/v1"

    def __init__(self) -> None:
        self.api_key = settings.FINNHUB_API_KEY
        self.last_latency = 0.0
        self._profile_cache: dict[str, tuple[float, dict[str, Any] | None]] = {}
        self.profile_ttl = 12 * 60 * 60

    async def get_company_profile(self, ticker: str) -> dict[str, Any] | None:
        if not self.api_key:
            logger.warning("Finnhub API key not configured; skipping profile fetch for %s", ticker)
            return None

        start_time = time.time()
        original_symbol = ticker.upper()

        cached = self._profile_cache.get(original_symbol)
        if cached and time.time() - cached[0] < self.profile_ttl:
            self.last_latency = (time.time() - start_time) * 1000
            logger.debug("Finnhub cache hit: %s", original_symbol)
            return cached[1]

        finnhub_symbol = to_finnhub_symbol(original_symbol)

        if finnhub_symbol != original_symbol:
            logger.info(
                "Finnhub symbol conversion: %s -> %s",
                original_symbol, finnhub_symbol,
            )

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0, connect=2.0)) as client:
                response = await client.get(
                    f"{self.BASE_URL}/stock/profile2",
                    params={"symbol": finnhub_symbol, "token": self.api_key},
                )
                self.last_latency = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    data = cast(dict[str, Any], response.json())
                    logger.info(
                        "Finnhub profile response for %s (finnhub_symbol=%s): %s",
                        original_symbol, finnhub_symbol,
                        json.dumps(data, default=str)[:500],
                    )
                    self._profile_cache[original_symbol] = (time.time(), data)
                    return data

                logger.warning(
                    "Finnhub profile returned status %d for %s (finnhub_symbol=%s): %s",
                    response.status_code, original_symbol, finnhub_symbol, response.text[:200],
                )
                return None
        except Exception as exc:
            self.last_latency = (time.time() - start_time) * 1000
            logger.error(
                "Finnhub profile fetch failed for %s (finnhub_symbol=%s): %s",
                original_symbol, finnhub_symbol, exc,
            )
            return None


finnhub_service = FinnhubService()
