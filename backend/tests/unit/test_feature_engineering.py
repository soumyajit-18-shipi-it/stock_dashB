import numpy as np
import pandas as pd
import pytest
from features.engineering import FeatureEngineer


@pytest.fixture
def sample_df() -> pd.DataFrame:
    dates = pd.date_range(start="2023-01-01", periods=100)
    data = {
        "Open": np.random.rand(100) * 100,
        "High": np.random.rand(100) * 100,
        "Low": np.random.rand(100) * 100,
        "Close": np.random.rand(100) * 100,
        "Volume": np.random.randint(1000, 10000, size=100),
    }
    return pd.DataFrame(data, index=dates)


class TestFeatureEngineering:
    def test_prepare_features(self, sample_df: pd.DataFrame) -> None:
        engineer = FeatureEngineer()
        df = engineer.prepare_features(sample_df)
        assert not df.empty
        assert "ma7" in df.columns
        assert "ma21" in df.columns
        assert "returns" in df.columns
        assert "lag1" in df.columns

    def test_get_feature_columns(self) -> None:
        engineer = FeatureEngineer()
        cols = engineer.get_feature_columns()
        assert "Close" in cols
        assert "ma7" in cols
        assert "volume_change" in cols

    def test_prepare_training_data(self, sample_df: pd.DataFrame) -> None:
        engineer = FeatureEngineer()
        X, y = engineer.prepare_training_data(sample_df)
        assert len(X) == len(y)
        assert not X.empty
        assert not y.empty

    def test_prepare_prediction_input(self, sample_df: pd.DataFrame) -> None:
        engineer = FeatureEngineer()
        X_pred = engineer.prepare_prediction_input(sample_df)
        assert len(X_pred) == 1
        assert "ma7" in X_pred.columns
