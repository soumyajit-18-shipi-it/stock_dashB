"""I/O orchestration for independently testable portfolio analytics."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import pandas as pd

from core.config import settings
from data.provider import StockDataProvider
from portfolio.analytics import PortfolioAnalyticsEngine
from portfolio.parser import PortfolioParser
from portfolio.types import HoldingPosition, PortfolioAnalysis
from services.ai_service import AIService, ai_service
from services.metadata_service import MetadataService, metadata_service


class PortfolioService:
    def __init__(
        self,
        data_provider: StockDataProvider | None = None,
        analytics: PortfolioAnalyticsEngine | None = None,
        parser: PortfolioParser | None = None,
        explanation_service: AIService | None = None,
        company_metadata: MetadataService | None = None,
    ) -> None:
        self.data_provider = data_provider or StockDataProvider()
        self.analytics = analytics or PortfolioAnalyticsEngine(
            settings.RISK_FREE_RATE
        )
        self.parser = parser or PortfolioParser()
        self.ai_service = explanation_service or ai_service
        self.company_metadata = company_metadata or metadata_service
        self.fetch_concurrency = 5

    def parse_csv(self, content: str) -> list[HoldingPosition]:
        return self.parser.parse_csv(content)

    async def analyze(
        self,
        positions: list[HoldingPosition],
        range_key: str = "5y",
    ) -> PortfolioAnalysis:
        normalized = [
            HoldingPosition(
                ticker=item.ticker.strip().upper(),
                quantity=item.quantity,
                average_cost=item.average_cost,
                weight=item.weight,
            )
            for item in positions
        ]
        semaphore = asyncio.Semaphore(self.fetch_concurrency)

        async def load(
            position: HoldingPosition,
        ) -> tuple[HoldingPosition, pd.Series | None, dict[str, Any], str | None]:
            async with semaphore:
                try:
                    history, info = await asyncio.gather(
                        asyncio.to_thread(
                            self.data_provider.get_stock_data,
                            position.ticker,
                            range_key,
                        ),
                        asyncio.to_thread(
                            self.data_provider.get_company_info,
                            position.ticker,
                        ),
                    )
                    company = await self.company_metadata.get_company_metadata(
                        position.ticker, info
                    )
                    info = {
                        **info,
                        "sector": info.get("sector") or company.sector,
                        "country": info.get("country") or company.country,
                        "marketCap": info.get("marketCap") or company.market_cap,
                    }
                    series = history["Close"].copy()
                    series.index = self._normalized_index(series.index)
                    series = series[~series.index.duplicated(keep="last")]
                    return position, series, info, None
                except Exception as exc:  # pylint: disable=broad-exception-caught
                    return position, None, {}, str(exc)

        loaded = await asyncio.gather(*(load(position) for position in normalized))
        valid_positions: list[HoldingPosition] = []
        series: list[pd.Series] = []
        metadata: dict[str, dict[str, Any]] = {}
        warnings: list[str] = []
        for position, price_series, info, error in loaded:
            if price_series is None:
                warnings.append(f"{position.ticker}: {error or 'data unavailable'}")
                continue
            valid_positions.append(position)
            series.append(price_series.rename(position.ticker))
            metadata[position.ticker] = info
        if not valid_positions:
            raise ValueError("No holdings have sufficient market data")
        if len(valid_positions) != len(normalized):
            if any(item.weight is not None for item in normalized):
                total = sum(item.weight or 0.0 for item in valid_positions)
                if total <= 0:
                    raise ValueError("Remaining holdings have no positive allocation")
                valid_positions = [
                    HoldingPosition(
                        ticker=item.ticker,
                        quantity=item.quantity,
                        average_cost=item.average_cost,
                        weight=(item.weight or 0.0) / total,
                    )
                    for item in valid_positions
                ]

        prices = pd.concat(series, axis=1).sort_index()
        benchmark = await self._benchmark_prices(range_key, valid_positions)
        return await asyncio.to_thread(
            self.analytics.analyze,
            valid_positions,
            prices,
            metadata,
            benchmark,
            warnings,
        )

    async def explain(self, analysis: PortfolioAnalysis) -> str:
        """Let the LLM explain computed facts; it cannot alter analytics."""
        payload = analysis.to_dict()
        compact = {
            "metrics": payload["metrics"],
            "largest_risks": payload["largest_risks"],
            "sector_exposure": payload["sector_exposure"],
            "best_holdings": payload["best_holdings"],
            "weakest_holdings": payload["weakest_holdings"],
            "rebalancing": payload["rebalancing"],
        }
        return await self.ai_service.complete_chat(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Explain the supplied deterministic portfolio analytics. "
                        "Do not invent values, change scores, or present personalized "
                        "financial advice. State uncertainty and use concise sections."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(compact, separators=(",", ":")),
                },
            ],
            provider="auto",
            temperature=0.1,
            max_tokens=900,
        )

    async def _benchmark_prices(
        self,
        range_key: str,
        positions: list[HoldingPosition],
    ) -> pd.Series | None:
        indian_count = sum(
            item.ticker.endswith((".NS", ".BO")) for item in positions
        )
        symbol = "^NSEI" if indian_count > len(positions) / 2 else "SPY"
        try:
            history = await asyncio.to_thread(
                self.data_provider.get_stock_data, symbol, range_key
            )
            series = history["Close"].copy()
            series.index = self._normalized_index(series.index)
            return series[~series.index.duplicated(keep="last")]
        except Exception:  # pylint: disable=broad-exception-caught
            return None

    @staticmethod
    def _normalized_index(index: pd.Index) -> pd.DatetimeIndex:
        values = pd.to_datetime(index, utc=True).tz_localize(None)
        return values.normalize()

