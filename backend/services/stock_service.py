import pandas as pd
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from ..data.provider import StockDataProvider
from ..features.engineering import FeatureEngineer
from ..ml.predictor import StockPredictor
from .finnhub_service import finnhub_service
from ..schemas import (
    StockResponse,
    CompanyProfile,
    StockPricePoint,
    PredictionResult,
    ModelMetrics,
    ModelEnum,
    DateRangeEnum
)

class StockService:
    def __init__(self):
        self.data_provider = StockDataProvider()
        self.feature_engineer = FeatureEngineer()
        self.predictor = StockPredictor()
        self.last_metrics = {}

    async def get_full_stock_analysis(
        self, 
        ticker: str, 
        range_key: DateRangeEnum = DateRangeEnum.ONE_YEAR, 
        model_type: ModelEnum = ModelEnum.LINEAR
    ) -> StockResponse:
        ticker = ticker.upper()
        start_time = time.time()

        # 1. Fetch Historical Data
        df = self.data_provider.get_stock_data(ticker, range_key.value)
        yahoo_latency = self.data_provider.last_latency
        
        # 2. Fetch Company Profile (Parallel-ish)
        finnhub_profile = await finnhub_service.get_company_profile(ticker)
        finnhub_latency = finnhub_service.last_latency
        
        yahoo_info = self.data_provider.get_company_info(ticker)
        
        # 3. Merge Profile Data with Fallbacks
        profile = self._merge_profile_data(ticker, yahoo_info, finnhub_profile, df)
        
        # 4. Feature Engineering
        df_features = self.feature_engineer.prepare_features(df)
        
        # 5. ML Prediction
        ml_start = time.time()
        prediction, metrics = self.predictor.predict(ticker, model_type, range_key.value)
        ml_latency = (time.time() - ml_start) * 1000
        
        # 6. Format History
        history = self._format_history(df_features)
        
        # Track metrics for debugging
        self.last_metrics = {
            "ticker": ticker,
            "yahoo_latency_ms": yahoo_latency,
            "finnhub_latency_ms": finnhub_latency,
            "ml_inference_ms": ml_latency,
            "total_time_ms": (time.time() - start_time) * 1000,
            "timestamp": time.time()
        }
        
        return StockResponse(
            ticker=ticker,
            profile=profile,
            history=history,
            prediction=prediction,
            metrics=metrics,
            confidence=prediction.confidence
        )

    def _merge_profile_data(self, ticker: str, yahoo: Dict[str, Any], finnhub: Optional[Dict[str, Any]], df: pd.DataFrame) -> CompanyProfile:
        finnhub = finnhub or {}
        last_close = float(df["Close"].iloc[-1]) if not df.empty else None
        
        return CompanyProfile(
            ticker=ticker,
            name=finnhub.get("name") or yahoo.get("longName") or yahoo.get("shortName") or ticker,
            sector=finnhub.get("finnhubIndustry") or yahoo.get("sector"),
            industry=finnhub.get("finnhubIndustry") or yahoo.get("industry"),
            market_cap=yahoo.get("marketCap") or (finnhub.get("marketCapitalization", 0) * 1000000 if finnhub.get("marketCapitalization") else None),
            current_price=yahoo.get("currentPrice") or yahoo.get("regularMarketPrice") or last_close,
            previous_close=yahoo.get("previousClose") or yahoo.get("regularMarketPreviousClose"),
            currency=yahoo.get("currency") or "USD",
            exchange=finnhub.get("exchange") or yahoo.get("exchange"),
            country=finnhub.get("country") or yahoo.get("country"),
            week_52_high=yahoo.get("fiftyTwoWeekHigh"),
            week_52_low=yahoo.get("fiftyTwoWeekLow")
        )

    def _format_history(self, df: pd.DataFrame) -> List[StockPricePoint]:
        history = []
        for idx, row in df.iterrows():
            history.append(StockPricePoint(
                date=idx.strftime("%Y-%m-%d") if isinstance(idx, (pd.Timestamp, datetime)) else str(idx),
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=int(row["Volume"]),
                ma7=float(row["ma7"]) if pd.notna(row.get("ma7")) else None,
                ma21=float(row["ma21"]) if pd.notna(row.get("ma21")) else None,
            ))
        return history

stock_service = StockService()
