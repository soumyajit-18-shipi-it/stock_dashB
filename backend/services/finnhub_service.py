import time
from typing import Any, cast

import httpx
from core.config import settings


class FinnhubService:
    BASE_URL = "https://finnhub.io/api/v1"

    def __init__(self) -> None:
        self.api_key = settings.FINNHUB_API_KEY
        self.last_latency = 0.0

    async def get_company_profile(self, ticker: str) -> dict[str, Any] | None:
        if not self.api_key:
            return None

        start_time = time.time()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/stock/profile2",
                    params={"symbol": ticker, "token": self.api_key},
                    timeout=10.0,
                )
                self.last_latency = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    return cast(dict[str, Any], response.json())
                return None
        except Exception:
            self.last_latency = (time.time() - start_time) * 1000
            return None


finnhub_service = FinnhubService()
