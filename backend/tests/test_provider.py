import pytest
from unittest.mock import MagicMock, patch
from data.provider import StockDataProvider
import pandas as pd

@pytest.fixture
def provider():
    return StockDataProvider()

def test_provider_returns_latest_daily_candle(provider):
    mock_ticker = MagicMock()
    
    # Mock history dataframe
    dates = pd.date_range(end=pd.Timestamp.now(), periods=5, freq='D')
    mock_df = pd.DataFrame({
        "Open": [150.0] * 5,
        "High": [155.0] * 5,
        "Low": [149.0] * 5,
        "Close": [152.0] * 5,
        "Volume": [1000000] * 5
    }, index=dates)
    mock_df.index.name = "Date"
    mock_ticker.history.return_value = mock_df
    
    # Mock fast_info
    mock_fast_info = MagicMock()
    mock_fast_info.last_price = 152.0
    mock_fast_info.currency = "USD"
    mock_fast_info.previous_close = 151.0
    mock_fast_info.year_high = 180.0
    mock_fast_info.year_low = 130.0
    mock_fast_info.market_cap = 2000000000000.0
    mock_fast_info.exchange = "NMS"
    # Support dict lookup
    mock_fast_info.__getitem__.side_effect = lambda key: getattr(mock_fast_info, key, None)
    
    mock_ticker.fast_info = mock_fast_info
    mock_ticker.info = {
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "longName": "Apple Inc."
    }

    with patch("yfinance.Ticker", return_value=mock_ticker):
        df = provider.get_stock_data("AAPL", "1mo", force_refresh=True)
        
        # Verify it returns a dataframe with data
        assert not df.empty
        assert "Close" in df.columns
        assert "Open" in df.columns
        assert "High" in df.columns
        assert "Low" in df.columns
        assert isinstance(df.index, pd.DatetimeIndex)

def test_provider_returns_missing_statistics(provider):
    mock_ticker = MagicMock()
    
    # Mock fast_info
    mock_fast_info = MagicMock()
    mock_fast_info.previous_close = 151.0
    mock_fast_info.year_high = 180.0
    mock_fast_info.year_low = 130.0
    mock_fast_info.market_cap = 2000000000000.0
    mock_fast_info.currency = "USD"
    mock_fast_info.exchange = "NMS"
    mock_fast_info.last_price = 152.0
    # Support dict lookup
    mock_fast_info.__getitem__.side_effect = lambda key: getattr(mock_fast_info, key, None)
    
    mock_ticker.fast_info = mock_fast_info
    mock_ticker.info = {
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "longName": "Apple Inc.",
        "previousClose": 151.0,
        "fiftyTwoWeekHigh": 180.0,
        "fiftyTwoWeekLow": 130.0,
        "marketCap": 2000000000000.0
    }

    with patch("yfinance.Ticker", return_value=mock_ticker):
        info = provider.get_company_info("AAPL")
        
        # Verify statistics are present
        assert "previousClose" in info
        assert info["previousClose"] is not None
        assert info["previousClose"] > 0
        
        assert "fiftyTwoWeekHigh" in info
        assert info["fiftyTwoWeekHigh"] is not None
        assert info["fiftyTwoWeekHigh"] > 0
        
        assert "fiftyTwoWeekLow" in info
        assert info["fiftyTwoWeekLow"] is not None
        assert info["fiftyTwoWeekLow"] > 0

