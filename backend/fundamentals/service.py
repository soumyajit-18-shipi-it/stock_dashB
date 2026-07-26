"""Normalize company fundamentals from Yahoo with Finnhub fallbacks."""

from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass
from typing import Any

from data.provider import StockDataProvider
from services.finnhub_service import FinnhubService, finnhub_service


@dataclass(frozen=True)
class FundamentalMetrics:
    revenue_growth: float | None = None
    eps_growth: float | None = None
    debt_to_equity: float | None = None
    return_on_equity: float | None = None
    return_on_assets: float | None = None
    current_ratio: float | None = None
    quick_ratio: float | None = None
    operating_margin: float | None = None
    profit_margin: float | None = None
    free_cash_flow: float | None = None
    peg_ratio: float | None = None
    pe_ratio: float | None = None
    forward_pe: float | None = None
    price_to_book: float | None = None
    dividend_yield: float | None = None
    institutional_ownership: float | None = None
    insider_ownership: float | None = None
    market_cap: float | None = None
    enterprise_value: float | None = None
    free_cash_flow_yield: float | None = None
    source_coverage: float = 0.0

    def to_dict(self) -> dict[str, float | None]:
        return asdict(self)


class FundamentalService:
    """Merge provider fields into consistent decimal units."""

    def __init__(
        self,
        data_provider: StockDataProvider | None = None,
        finnhub: FinnhubService | None = None,
    ) -> None:
        self.data_provider = data_provider or StockDataProvider()
        self.finnhub = finnhub or finnhub_service

    async def get_metrics(self, ticker: str) -> FundamentalMetrics:
        yahoo, finnhub = await asyncio.gather(
            asyncio.to_thread(self.data_provider.get_company_info, ticker),
            self.finnhub.get_basic_financials(ticker),
        )
        return self.from_provider_data(yahoo, finnhub)

    def from_provider_data(
        self, yahoo: dict[str, Any], finnhub: dict[str, Any] | None = None
    ) -> FundamentalMetrics:
        finnhub = finnhub or {}
        market_cap = self._market_cap(
            yahoo.get("marketCap"), finnhub.get("marketCapitalization")
        )
        free_cash_flow = self._number(yahoo.get("freeCashflow"))
        free_cash_flow_yield = (
            free_cash_flow / market_cap
            if free_cash_flow is not None and market_cap and market_cap > 0
            else None
        )
        values: dict[str, float | None] = {
            "revenue_growth": self._provider_decimal(
                yahoo.get("revenueGrowth"),
                finnhub.get("revenueGrowthTTMYoy"),
                finnhub.get("revenueGrowth3Y"),
            ),
            "eps_growth": self._provider_decimal(
                yahoo.get("earningsGrowth"),
                finnhub.get("epsGrowthTTMYoy"),
                finnhub.get("epsGrowth3Y"),
            ),
            "debt_to_equity": self._ratio(
                yahoo.get("debtToEquity"),
                finnhub.get("totalDebt/totalEquityAnnual"),
            ),
            "return_on_equity": self._provider_decimal(
                yahoo.get("returnOnEquity"), finnhub.get("roeTTM")
            ),
            "return_on_assets": self._provider_decimal(
                yahoo.get("returnOnAssets"), finnhub.get("roaTTM")
            ),
            "current_ratio": self._number(
                yahoo.get("currentRatio"), finnhub.get("currentRatioAnnual")
            ),
            "quick_ratio": self._number(
                yahoo.get("quickRatio"), finnhub.get("quickRatioAnnual")
            ),
            "operating_margin": self._provider_decimal(
                yahoo.get("operatingMargins"),
                finnhub.get("operatingMarginTTM"),
            ),
            "profit_margin": self._provider_decimal(
                yahoo.get("profitMargins"), finnhub.get("netProfitMarginTTM")
            ),
            "free_cash_flow": free_cash_flow,
            "peg_ratio": self._number(
                yahoo.get("trailingPegRatio"), finnhub.get("pegTTM")
            ),
            "pe_ratio": self._number(
                yahoo.get("trailingPE"), finnhub.get("peTTM")
            ),
            "forward_pe": self._number(yahoo.get("forwardPE")),
            "price_to_book": self._number(
                yahoo.get("priceToBook"), finnhub.get("pbAnnual")
            ),
            "dividend_yield": self._provider_decimal(
                yahoo.get("dividendYield"),
                finnhub.get("dividendYieldIndicatedAnnual"),
            ),
            "institutional_ownership": self._number(
                yahoo.get("heldPercentInstitutions")
            ),
            "insider_ownership": self._number(yahoo.get("heldPercentInsiders")),
            "market_cap": market_cap,
            "enterprise_value": self._number(yahoo.get("enterpriseValue")),
            "free_cash_flow_yield": free_cash_flow_yield,
        }
        populated = sum(value is not None for value in values.values())
        coverage = populated / len(values)
        return FundamentalMetrics(**values, source_coverage=round(coverage, 6))

    @staticmethod
    def _number(*values: Any) -> float | None:
        for value in values:
            try:
                parsed = float(value)
            except (TypeError, ValueError):
                continue
            if parsed == parsed:
                return parsed
        return None

    @classmethod
    def _provider_decimal(
        cls, yahoo_value: Any, *finnhub_values: Any
    ) -> float | None:
        yahoo = cls._number(yahoo_value)
        if yahoo is not None:
            return yahoo
        finnhub = cls._number(*finnhub_values)
        if finnhub is None:
            return None
        return finnhub / 100.0

    @classmethod
    def _market_cap(cls, yahoo_value: Any, finnhub_value: Any) -> float | None:
        yahoo = cls._number(yahoo_value)
        if yahoo is not None:
            return yahoo
        finnhub = cls._number(finnhub_value)
        return finnhub * 1_000_000.0 if finnhub is not None else None

    @classmethod
    def _ratio(cls, *values: Any) -> float | None:
        value = cls._number(*values)
        if value is None:
            return None
        return value / 100.0 if abs(value) > 10.0 else value

