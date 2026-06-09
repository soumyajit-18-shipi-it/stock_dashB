import pandas as pd
import pytest
from src.core.data_processor import DataProcessor

def test_calculate_moving_averages():
    data = {
        'Close': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    }
    df = pd.DataFrame(data)
    df_processed = DataProcessor.calculate_moving_averages(df)
    
    # MA7 at index 6 (7th element) should be (10+20+30+40+50+60+70)/7 = 40
    assert df_processed['MA7'].iloc[6] == 40
    # MA21 should be NaN for this small dataset
    assert pd.isna(df_processed['MA21'].iloc[9])

def test_dataframe_to_records():
    data = {
        'Open': [10], 'High': [15], 'Low': [5], 'Close': [12], 'Volume': [1000],
        'MA7': [11], 'MA21': [10]
    }
    df = pd.DataFrame(data, index=pd.to_datetime(['2023-01-01']))
    records = DataProcessor.dataframe_to_records(df)
    
    assert len(records) == 1
    assert records[0].date == '2023-01-01'
    assert records[0].close == 12.0
    assert records[0].ma7 == 11.0
