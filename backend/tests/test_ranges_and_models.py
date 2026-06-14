import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np
import os
from data.provider import StockDataProvider
from ml.predictor import StockPredictor
from schemas import ModelEnum

@pytest.fixture
def provider():
    return StockDataProvider()

@pytest.fixture
def predictor():
    return StockPredictor()

def test_chart_ranges_return_different_counts(provider):
    # Mock yfinance chart fetch
    mock_ticker = MagicMock()
    
    # We define history generator for different ranges
    def mock_history(period, interval="1d"):
        # Map period to counts
        count_map = {"1mo": 20, "6mo": 120, "1y": 252, "5y": 1260}
        n_days = count_map.get(period, 252)
        dates = pd.date_range(end=pd.Timestamp.now(), periods=n_days, freq='D')
        df = pd.DataFrame({
            "Open": [150.0] * n_days,
            "High": [155.0] * n_days,
            "Low": [149.0] * n_days,
            "Close": [152.0] * n_days,
            "Volume": [1000000] * n_days
        }, index=dates)
        df.index.name = "Date"
        return df

    mock_ticker.history.side_effect = mock_history
    
    mock_fast_info = MagicMock()
    mock_fast_info.last_price = 152.0
    mock_fast_info.currency = "USD"
    mock_fast_info.previous_close = 151.0
    mock_fast_info.year_high = 180.0
    mock_fast_info.year_low = 130.0
    mock_fast_info.market_cap = 2000000000000.0
    mock_fast_info.exchange = "NMS"
    mock_fast_info.__getitem__.side_effect = lambda key: getattr(mock_fast_info, key, None)
    mock_ticker.fast_info = mock_fast_info

    with patch("yfinance.Ticker", return_value=mock_ticker):
        df_1m = provider.get_stock_data("AAPL", "1m", force_refresh=True)
        df_6m = provider.get_stock_data("AAPL", "6m", force_refresh=True)
        df_1y = provider.get_stock_data("AAPL", "1y", force_refresh=True)
        df_5y = provider.get_stock_data("AAPL", "5y", force_refresh=True)
        
        # Verify counts are different
        assert len(df_1m) == 20
        assert len(df_6m) == 120
        assert len(df_1y) == 252
        assert len(df_5y) == 1260
        
        assert len(df_1m) < len(df_6m) < len(df_1y) < len(df_5y)

def test_models_train_and_predict_independently(predictor):
    # Mock data provider to return enough data points for training (e.g. 100 points)
    n_days = 100
    dates = pd.date_range(end=pd.Timestamp.now(), periods=n_days, freq='D')
    
    # Generate some slightly different values to make training realistic
    df = pd.DataFrame({
        "Open": np.linspace(150.0, 170.0, n_days),
        "High": np.linspace(155.0, 175.0, n_days),
        "Low": np.linspace(149.0, 169.0, n_days),
        "Close": np.linspace(152.0, 172.0, n_days),
        "Volume": [1000000] * n_days
    }, index=dates)
    df.index.name = "Date"
    
    # Set attributes
    df.attrs["metadata"] = {
        "regularMarketPrice": 172.0,
        "currency": "USD",
        "previousClose": 171.0,
        "fiftyTwoWeekHigh": 180.0,
        "fiftyTwoWeekLow": 130.0,
        "exchangeName": "NMS"
    }

    # Patch data provider to return this dataframe
    with patch.object(predictor.data_provider, "get_stock_data", return_value=df):
        # Predict using Linear Regression
        pred_lin, metrics_lin = predictor.predict("AAPL", ModelEnum.LINEAR, "1y")
        
        # Predict using Random Forest
        pred_rf, metrics_rf = predictor.predict("AAPL", ModelEnum.RANDOM_FOREST, "1y")
        
        # Assert model paths contain ticker and range
        path_lin = predictor._get_model_path(ModelEnum.LINEAR, "AAPL", "1y")
        path_rf = predictor._get_model_path(ModelEnum.RANDOM_FOREST, "AAPL", "1y")
        
        assert "aapl_1y_linear.pkl" in path_lin
        assert "aapl_1y_random_forest.pkl" in path_rf
        
        # Verify predictions were generated
        assert pred_lin.predicted_price > 0
        assert pred_rf.predicted_price > 0
        
        # Since they are different model architectures trained on linear-like features,
        # their predictions should be computed independently.
        assert pred_lin.model_used == "linear"
        assert pred_rf.model_used == "rf"

