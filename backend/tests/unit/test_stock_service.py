from unittest.mock import AsyncMock, patch
import pandas as pd
import pytest
from schemas import (
    DateRangeEnum,
    ModelEnum,
    ModelMetrics,
    PredictionResult,
    TrendDirection,
)
from services.stock_service import StockService


@pytest.mark.asyncio
async def test_stock_service_full_analysis() -> None:
    svc = StockService()

    # Mock historical dataframe
    mock_df = pd.DataFrame(
        {
            "Open": [100.0, 101.0],
            "High": [105.0, 106.0],
            "Low": [98.0, 99.0],
            "Close": [102.0, 103.0],
            "Volume": [1000, 1100],
        },
        index=pd.date_range("2026-06-01", periods=2),
    )
    mock_df.attrs["metadata"] = {"longName": "Test Inc."}

    # Mock predictor
    mock_pred = PredictionResult(
        predicted_price=104.0,
        trend=TrendDirection.INCREASE,
        confidence=0.8,
        model_used="linear",
    )
    mock_metrics = ModelMetrics(rmse=1.0, mae=0.8, r2=0.9)

    # Mock finnhub_service
    mock_finnhub = {"name": "Test Inc.", "marketCapitalization": 1.0}

    with (
        patch.object(
            svc.data_provider, "get_stock_data", return_value=mock_df
        ) as mock_get_stock_data,
        patch.object(
            svc.data_provider,
            "get_company_info",
            return_value={"marketCap": 1000000},
        ) as mock_get_company_info,
        patch.object(
            svc.predictor, "predict", return_value=(mock_pred, mock_metrics)
        ) as mock_predict,
        patch("services.stock_service.finnhub_service") as mock_finnhub_svc,
    ):
        svc.data_provider.last_latency = 100.0
        mock_finnhub_svc.get_company_profile = AsyncMock(return_value=mock_finnhub)
        mock_finnhub_svc.last_latency = 50.0

        res = await svc.get_full_stock_analysis(
            "AAPL", DateRangeEnum.ONE_YEAR, ModelEnum.LINEAR
        )
        assert res.ticker == "AAPL"
        assert res.profile.name == "Test Inc."
        assert len(res.history) == 2
        assert res.prediction.predicted_price == 104.0
        assert res.confidence == 0.8

        mock_get_stock_data.assert_called_once()
        mock_get_company_info.assert_called_once()
        mock_predict.assert_called_once()
