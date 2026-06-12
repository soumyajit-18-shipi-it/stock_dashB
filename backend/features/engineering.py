import pandas as pd
from features.technical_indicators import TechnicalIndicators


class FeatureEngineer:
    def __init__(self) -> None:
        self.indicators = TechnicalIndicators()

    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df = self.indicators.add_all_indicators(df)
        df["returns"] = df["Close"].pct_change()
        df["lag1"] = df["Close"].shift(1)
        df["lag2"] = df["Close"].shift(2)
        df["lag3"] = df["Close"].shift(3)
        df["lag4"] = df["Close"].shift(4)
        df["lag5"] = df["Close"].shift(5)
        df["volume_change"] = df["Volume"].pct_change()
        df = df.dropna()
        return df

    def get_feature_columns(self) -> list[str]:
        return [
            "Close",
            "Volume",
            "ma7",
            "ma21",
            "returns",
            "lag1",
            "lag2",
            "lag3",
            "lag4",
            "lag5",
            "volume_change",
        ]

    def prepare_training_data(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
        df = self.prepare_features(df)
        feature_cols = self.get_feature_columns()
        X = df[feature_cols].copy()
        y = df["Close"].shift(-1)
        valid_idx = ~y.isna()
        X = X[valid_idx]
        y = y[valid_idx]
        return X, y

    def prepare_prediction_input(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.prepare_features(df)
        feature_cols = self.get_feature_columns()
        return df[feature_cols].tail(1)
