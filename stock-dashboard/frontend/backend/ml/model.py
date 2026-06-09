import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from typing import Tuple, Literal

class StockPredictor:
    def __init__(self, model_type: str = "linear"):
        self.model_type = model_type
        if model_type == "rf":
            self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        else:
            self.model = LinearRegression()

    def train_and_predict(self, df: pd.DataFrame) -> Tuple[float, str, float]:
        """
        Trains the model on historical data and predicts the next day's price.
        Returns: (predicted_price, trend, current_price)
        """
        # Features: lags, day_of_week, month
        feature_cols = [col for col in df.columns if 'lag_' in col] + ['day_of_week', 'month']
        X = df[feature_cols]
        y = df['Close']
        
        # Train on all available data (simplification for this dashboard)
        self.model.fit(X, y)
        
        # Prepare feature for next day prediction (using the last available data point)
        last_row = df.iloc[-1]
        current_price = last_row['Close']
        
        # Next features: lag_1 becomes last_row['Close'], lag_2 becomes last_row['lag_1'], etc.
        next_features = {}
        next_features['lag_1'] = last_row['Close']
        for i in range(2, 6):
            next_features[f'lag_{i}'] = last_row[f'lag_{i-1}']
            
        # For date features, we'd ideally use next business day, but using last row + 1 for simplicity
        next_features['day_of_week'] = (last_row['day_of_week'] + 1) % 7
        next_features['month'] = last_row['month'] # simplified
        
        X_next = pd.DataFrame([next_features], columns=feature_cols)
        predicted_price = float(self.model.predict(X_next)[0])
        
        trend = "increase" if predicted_price > current_price else "decrease"
        
        return predicted_price, trend, current_price
