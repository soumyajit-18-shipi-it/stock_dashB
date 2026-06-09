import pandas as pd
import numpy as np
from typing import List, Dict, Any

def apply_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates technical indicators like 7-day and 21-day moving averages.
    """
    df = df.copy()
    df['ma7'] = df['Close'].rolling(window=7).mean()
    df['ma21'] = df['Close'].rolling(window=21).mean()
    return df

def prepare_ml_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepares features for the ML model (Lag features, etc.).
    """
    df = df.copy()
    # Use Close price as target, and creates lags as features
    for i in range(1, 6):
        df[f'lag_{i}'] = df['Close'].shift(i)
    
    # Simple features
    df['day_of_week'] = df.index.dayofweek
    df['month'] = df.index.month
    
    # Remove rows with NaN values resulting from rolling/shifting
    df = df.dropna()
    return df
