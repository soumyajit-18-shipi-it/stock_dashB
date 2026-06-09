import pandas as pd
import numpy as np

class FeatureEngineer:
    @staticmethod
    def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepares features for ML models.
        Features: Lagged Close, Lagged Volume, MA7, MA21.
        Target: Next day Close.
        """
        df = df.copy()
        
        # Calculate MAs if not already present
        if 'MA7' not in df.columns:
            df['MA7'] = df['Close'].rolling(window=7).mean()
        if 'MA21' not in df.columns:
            df['MA21'] = df['Close'].rolling(window=21).mean()
            
        # Create target (Shifted Close)
        df['Target'] = df['Close'].shift(-1)
        
        # Drop rows with NaN (due to MAs and Shift)
        # We keep the last row without Target for prediction
        predict_row = df.iloc[[-1]].copy()
        train_df = df.dropna()
        
        return train_df, predict_row

    @staticmethod
    def get_feature_matrices(df: pd.DataFrame):
        """
        Splits dataframe into X (features) and y (target).
        """
        features = ['Close', 'Volume', 'MA7', 'MA21']
        X = df[features].values
        y = df['Target'].values
        return X, y
