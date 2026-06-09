import pandas as pd
from typing import List
from core.models import StockRecord

class DataProcessor:
    @staticmethod
    def calculate_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates 7-day and 21-day moving averages.
        """
        df = df.copy()
        df['MA7'] = df['Close'].rolling(window=7).mean()
        df['MA21'] = df['Close'].rolling(window=21).mean()
        return df

    @staticmethod
    def dataframe_to_records(df: pd.DataFrame) -> List[StockRecord]:
        """
        Converts pandas DataFrame to a list of StockRecord pydantic models.
        """
        records = []
        for index, row in df.iterrows():
            records.append(StockRecord(
                date=index.strftime('%Y-%m-%d'),
                open=float(row['Open']),
                high=float(row['High']),
                low=float(row['Low']),
                close=float(row['Close']),
                volume=int(row['Volume']),
                ma7=float(row['MA7']) if not pd.isna(row['MA7']) else None,
                ma21=float(row['MA21']) if not pd.isna(row['MA21']) else None
            ))
        return records
