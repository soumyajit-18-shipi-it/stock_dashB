import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any

import pandas as pd
from data.provider import StockDataProvider
from features.engineering import FeatureEngineer
from ml.predictor import StockPredictor
from schemas import (
    CompanyProfile,
    DateRangeEnum,
    ModelEnum,
    ModelMetrics,
    PredictionResult,
    StockPricePoint,
    StockResponse,
    TrendDirection,
)
from services.finnhub_service import finnhub_service
from services.metadata_service import MetadataService, ProviderResult
from services.symbol_converter import is_indian_ticker


class StockService:
    def __init__(self) -> None:
        self.data_provider = StockDataProvider()
        self.feature_engineer = FeatureEngineer()
        self.predictor = StockPredictor()
        self.metadata_service = MetadataService()
        self.last_metrics: dict[str, Any] = {}
        self._analysis_cache: dict[tuple[str, str, str], tuple[float, StockResponse]] = {}
        self.response_ttl_seconds = 300
        self.logger = logging.getLogger("stock_dashboard")

    async def get_full_stock_analysis(
        self,
        ticker: str,
        range_key: DateRangeEnum = DateRangeEnum.ONE_YEAR,
        model_type: ModelEnum = ModelEnum.LINEAR,
    ) -> StockResponse:
        ticker = ticker.upper()
        start_time = time.time()
        cache_key = (ticker, range_key.value, model_type.value)
        cached = self._analysis_cache.get(cache_key)
        if cached and time.time() - cached[0] < self.response_ttl_seconds:
            self.last_metrics = {
                "ticker": ticker,
                "cache_hit": True,
                "total_time_ms": (time.time() - start_time) * 1000,
                "timestamp": time.time(),
            }
            self.logger.info("Stock analysis cache hit: ticker=%s", ticker)
            return cached[1]

        self.logger.info("Stock analysis cache miss: ticker=%s", ticker)

        # 1. Fetch independent provider data concurrently.
        df, yahoo_info, finnhub_profile = await asyncio.gather(
            asyncio.to_thread(
                self.data_provider.get_stock_data, ticker, range_key.value
            ),
            asyncio.to_thread(self.data_provider.get_company_info, ticker),
            finnhub_service.get_company_profile(ticker),
        )
        yahoo_latency = self.data_provider.last_latency
        finnhub_latency = finnhub_service.last_latency

        self.logger.info(
            "Provider data received for %s: yahoo_info keys=%s, finnhub_profile=%s",
            ticker,
            list(yahoo_info.keys()) if yahoo_info else "N/A",
            "present" if finnhub_profile else "None",
        )
        if yahoo_info:
            self.logger.info(
                "Yahoo info sector=%s industry=%s marketCap=%s longName=%s",
                yahoo_info.get("sector"),
                yahoo_info.get("industry"),
                yahoo_info.get("marketCap"),
                yahoo_info.get("longName"),
            )
        if finnhub_profile:
            self.logger.info(
                "Finnhub profile sector=%s industry=%s marketCap=%s name=%s",
                finnhub_profile.get("sector"),
                finnhub_profile.get("finnhubIndustry"),
                finnhub_profile.get("marketCapitalization"),
                finnhub_profile.get("name"),
            )

        # 2. Run metadata service for fallback chain (Finnhub → Yahoo → Screener.in)
        provider_result = await self.metadata_service.get_company_metadata(
            ticker, yahoo_info,
        )
        for diag in self.metadata_service.last_diagnostics:
            self.logger.info(
                "Metadata provider=%s status=%s fields=%s reason=%s latency=%.0fms",
                diag.provider, diag.status,
                ",".join(diag.fields_returned) or "-",
                diag.reason or "-", diag.latency_ms,
            )

        # 3. Merge Profile Data with Fallbacks
        profile = self._merge_profile_data(
            ticker, yahoo_info, finnhub_profile, df, provider_result,
        )

        # 3. Feature Engineering for Chart
        df_chart = self.feature_engineer.indicators.add_all_indicators(df)

        # 4. ML Prediction
        ml_start = time.time()
        try:
            prediction_df = df
            if range_key == DateRangeEnum.ONE_MONTH and len(df) < 60:
                prediction_df = await asyncio.to_thread(
                    self.data_provider.get_stock_data, ticker, "1y"
                )
            prediction, metrics = await asyncio.to_thread(
                self.predictor.predict_from_data,
                ticker,
                model_type,
                range_key.value,
                prediction_df,
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self.logger.warning("Prediction fallback used for %s: %s", ticker, exc)
            prediction, metrics = self._fallback_prediction(df, model_type)
        ml_latency = (time.time() - ml_start) * 1000

        # 5. Format History
        history = self._format_history(df_chart)

        # Track metrics for debugging
        self.last_metrics = {
            "ticker": ticker,
            "yahoo_latency_ms": yahoo_latency,
            "finnhub_latency_ms": finnhub_latency,
            "ml_inference_ms": ml_latency,
            "total_time_ms": (time.time() - start_time) * 1000,
            "cache_hit": False,
            "timestamp": time.time(),
        }

        response = StockResponse(
            ticker=ticker,
            profile=profile,
            history=history,
            prediction=prediction,
            metrics=metrics,
            confidence=prediction.confidence,
        )
        self._analysis_cache[cache_key] = (time.time(), response)
        return response

    def _merge_profile_data(
        self,
        ticker: str,
        yahoo: dict[str, Any],
        finnhub: dict[str, Any] | None,
        df: pd.DataFrame,
        provider_result: ProviderResult | None = None,
    ) -> CompanyProfile:
        finnhub = finnhub or {}
        meta = df.attrs.get("metadata", {})
        last_close = float(df["Close"].iloc[-1]) if not df.empty else None

        # ---- Market Cap (priority: provider chain → Finnhub → yahoo → manual) ----
        market_cap = self._first_number(
            provider_result.market_cap if provider_result else None,
            (
                finnhub.get("marketCapitalization") * 1000000
                if finnhub.get("marketCapitalization")
                else None
            ),
            yahoo.get("marketCap"),
        )

        # If marketCap is still missing, try to calculate from sharesOutstanding * currentPrice
        if not market_cap:
            shares = self._first_number(
                finnhub.get("shareOutstanding"),
                yahoo.get("sharesOutstanding"),
                yahoo.get("impliedSharesOutstanding"),
            )
            price = self._first_number(
                yahoo.get("currentPrice"),
                yahoo.get("regularMarketPrice"),
                meta.get("regularMarketPrice"),
                last_close,
            )
            if shares and price:
                market_cap = shares * price
                self.logger.info(
                    "Calculated market cap for %s: shares=%s * price=%s = %s",
                    ticker, shares, price, market_cap,
                )

        # ---- Sector (priority: provider chain → Finnhub → yahoo) ----
        sector = self._first_text(
            provider_result.sector if provider_result else None,
            finnhub.get("sector"),
            yahoo.get("sector"),
            finnhub.get("finnhubIndustry"),
        )

        # ---- Industry (priority: provider chain → Finnhub → yahoo) ----
        industry = self._first_text(
            provider_result.industry if provider_result else None,
            finnhub.get("finnhubIndustry"),
            yahoo.get("industry"),
            finnhub.get("sector"),
        )

        # ---- Website ----
        website = self._first_text(
            finnhub.get("weburl"),
            yahoo.get("website"),
        )

        # ---- Logo ----
        logo = self._first_text(
            finnhub.get("logo"),
            yahoo.get("logo"),
            yahoo.get("logo_url"),
        )

        # Fallback: construct logo URL from website via Clearbit
        if not logo and website:
            domain = website.replace("https://", "").replace("http://", "").split("/")[0]
            if domain:
                logo = f"https://logo.clearbit.com/{domain}"

        # ---- Name ----
        name = self._first_text(
            finnhub.get("name"),
            meta.get("longName"),
            yahoo.get("longName"),
            yahoo.get("shortName"),
            ticker,
        )

        # ---- Currency (default based on exchange/ticker) ----
        currency = self._first_text(
            finnhub.get("currency"),
            meta.get("currency"),
            yahoo.get("currency"),
        )
        if not currency:
            currency = "INR" if is_indian_ticker(ticker) else "USD"

        # ---- Exchange ----
        exchange = self._first_text(
            finnhub.get("exchange"),
            meta.get("exchangeName"),
            yahoo.get("exchange"),
        )

        # ---- Price ----
        current_price = self._first_number(
            meta.get("regularMarketPrice"),
            yahoo.get("regularMarketPrice"),
            yahoo.get("currentPrice"),
            last_close,
        )

        previous_close = self._first_number(
            meta.get("previousClose"),
            yahoo.get("previousClose"),
        )

        # ---- 52-week range ----
        week_52_high = self._first_number(
            meta.get("fiftyTwoWeekHigh"),
            yahoo.get("fiftyTwoWeekHigh"),
        )
        week_52_low = self._first_number(
            meta.get("fiftyTwoWeekLow"),
            yahoo.get("fiftyTwoWeekLow"),
        )

        # ---- Country ----
        country = self._first_text(
            finnhub.get("country"),
            yahoo.get("country"),
        )

        self.logger.info(
            "Merged profile for %s: sector=%s industry=%s market_cap=%s name=%s logo=%s website=%s",
            ticker, sector, industry, market_cap, name,
            "present" if logo else None,
            "present" if website else None,
        )

        return CompanyProfile(
            ticker=ticker,
            name=name,
            sector=sector,
            industry=industry,
            market_cap=market_cap,
            current_price=current_price,
            previous_close=previous_close,
            currency=currency,
            exchange=exchange,
            country=country,
            week_52_high=week_52_high,
            week_52_low=week_52_low,
            logo=logo,
            website=website,
        )

    def _fallback_prediction(
        self, df: pd.DataFrame, model_type: ModelEnum
    ) -> tuple[PredictionResult, ModelMetrics]:
        last_close = float(df["Close"].iloc[-1]) if not df.empty else 0.0
        return (
            PredictionResult(
                predicted_price=round(last_close, 4),
                trend=TrendDirection.INCREASE,
                confidence=0.0,
                model_used=f"{model_type.value}_fallback",
            ),
            ModelMetrics(rmse=0.0, mae=0.0, r2=0.0),
        )

    def _first_text(self, *values: Any) -> str | None:
        for value in values:
            if value is None:
                continue
            text = str(value).strip()
            if text and text.lower() not in {"n/a", "na", "none", "null", "-"}:
                return text
        return None

    def _first_number(self, *values: Any) -> float | None:
        for value in values:
            if value is None:
                continue
            try:
                number = float(value)
            except (TypeError, ValueError):
                continue
            if pd.notna(number) and number > 0:
                return number
        return None

    def _format_history(self, df: pd.DataFrame) -> list[StockPricePoint]:
        history = []
        for idx, row in df.iterrows():
            history.append(
                StockPricePoint(
                    date=idx.strftime("%Y-%m-%d")
                    if isinstance(idx, pd.Timestamp | datetime)
                    else str(idx),
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=int(row["Volume"]),
                    ma7=float(row["ma7"]) if pd.notna(row.get("ma7")) else None,
                    ma21=float(row["ma21"]) if pd.notna(row.get("ma21")) else None,
                )
            )
        return history


stock_service = StockService()
