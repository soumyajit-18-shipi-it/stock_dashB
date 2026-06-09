import yfinance as yf
import pandas as pd
from typing import Tuple, Dict, Any

def fetch_stock_raw_data(ticker: str, period: str = "1y") -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Fetches historical data and info for a given ticker.
    """
    stock = yf.Ticker(ticker)
    
    # Fetch historical data
    # yfinance periods: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    # Frontend uses: 1m, 6m, 1y, 5y
    yf_period = period
    if period == "1m":
        yf_period = "1mo"
    elif period == "6m":
        yf_period = "6mo"
        
    df = stock.history(period=yf_period)
    
    # Fetch info
    info = stock.info
    
    return df, info

def get_company_profile(info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts relevant profile information from yfinance info dict.
    """
    return {
        "name": info.get("longName", "N/A"),
        "sector": info.get("sector", "N/A"),
        "market_cap": info.get("marketCap", 0),
        "high_52w": info.get("fiftyTwoWeekHigh", 0.0),
        "low_52w": info.get("fiftyTwoWeekLow", 0.0),
    }
