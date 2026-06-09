import yfinance as yf
import pandas as pd
from typing import Tuple, Optional

class YFinanceService:
    @staticmethod
    def fetch_data(ticker: str, period: str = "1y") -> Tuple[pd.DataFrame, dict]:
        """
        Fetches historical data and company info from yfinance.
        """
        stock = yf.Ticker(ticker)
        
        # Fetch history
        df = stock.history(period=period)
        if df.empty:
            raise ValueError(f"No data found for ticker: {ticker}")
            
        # Fetch info
        info = stock.info
        
        return df, info

    @staticmethod
    def get_company_profile(info: dict) -> dict:
        """
        Extracts relevant company metadata from yfinance info dict.
        """
        return {
            "name": info.get("longName", "N/A"),
            "sector": info.get("sector", "N/A"),
            "market_cap": info.get("marketCap", 0),
            "high_52w": info.get("fiftyTwoWeekHigh", 0),
            "low_52w": info.get("fiftyTwoWeekLow", 0)
        }
