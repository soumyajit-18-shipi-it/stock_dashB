import pytest
import pandas as pd
import numpy as np
from features.engineering import FeatureEngineer


class TestFeatureEngineer:
    def setup_method(self):
        np.random.seed(42)
        n = 100
        self.df = pd.DataFrame({
            "Close": 100 + np.cumsum(np.random.randn(n) * 2),
            "Volume": 1000000 + np.random.randint(-100000, 100000, n)
        })

    def test_prepare_features(self):
        engineer = FeatureEngineer()
        result = engineer.prepare_features(self.df)
        assert "ma7" in result.columns
        assert "ma21" in result.columns
        assert "returns" in result.columns
        assert "lag1" in result.columns
        assert "lag2" in result.columns
        assert len(result) < len(self.df)

    def test_get_feature_columns(self):
        engineer = FeatureEngineer()
        columns = engineer.get_feature_columns()
        assert len(columns) == 11
        assert "Close" in columns
        assert "Volume" in columns
        assert "ma7" in columns
        assert "ma21" in columns

    def test_prepare_training_data(self):
        engineer = FeatureEngineer()
        X, y = engineer.prepare_training_data(self.df)
        assert X.shape[0] == y.shape[0]
        assert X.shape[1] == 11

    def test_prepare_prediction_input(self):
        engineer = FeatureEngineer()
        result = engineer.prepare_prediction_input(self.df)
        assert result.shape[0] == 1
        assert result.shape[1] == 11
