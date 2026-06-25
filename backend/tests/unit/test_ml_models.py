import os
import tempfile

import numpy as np
import pandas as pd
import pytest
from features.engineering import FeatureEngineer
from ml.data_cleaning import sanitize_features, validate_training_matrix
from ml.linear_model import LinearRegressionModel
from ml.random_forest_model import RandomForestModel


class TestMLModels:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.engineer = FeatureEngineer()
        dates = pd.date_range(start="2023-01-01", periods=100)
        data = {
            "Open": np.random.rand(100) * 100,
            "High": np.random.rand(100) * 100,
            "Low": np.random.rand(100) * 100,
            "Close": np.random.rand(100) * 100,
            "Volume": np.random.randint(1000, 10000, size=100),
        }
        df = pd.DataFrame(data, index=dates)
        self.X, self.y = self.engineer.prepare_training_data(df)

    def test_linear_regression_train_predict(self) -> None:
        model = LinearRegressionModel()
        model.train(self.X, self.y)
        assert model.is_trained()

        X_pred = self.X.iloc[-1:]
        prediction = model.predict(X_pred)
        assert len(prediction) == 1
        assert isinstance(prediction[0], int | float)

    def test_random_forest_train_predict(self) -> None:
        model = RandomForestModel()
        model.train(self.X, self.y)
        assert model.is_trained()

        X_pred = self.X.iloc[-1:]
        prediction = model.predict(X_pred)
        assert len(prediction) == 1
        assert isinstance(prediction[0], int | float)

    def test_linear_regression_save_load(self) -> None:
        model = LinearRegressionModel()
        model.train(self.X, self.y)

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            model.save(tmp.name)
            new_model = LinearRegressionModel()
            assert new_model.load(tmp.name)
            assert new_model.is_trained()
        os.unlink(tmp.name)

    def test_random_forest_save_load(self) -> None:
        model = RandomForestModel()
        model.train(self.X, self.y)

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            model.save(tmp.name)
            new_model = RandomForestModel()
            assert new_model.load(tmp.name)
            assert new_model.is_trained()
        os.unlink(tmp.name)

    def test_confidence_score(self) -> None:
        model = LinearRegressionModel()
        model.train(self.X, self.y)
        confidence = model.get_confidence_score()
        assert 0 <= confidence <= 1

    def test_training_matrix_sanitizes_non_finite_values(self) -> None:
        X = self.X.copy().astype(float)
        y = self.y.copy()
        X.iloc[0, 0] = np.inf
        X.iloc[1, 1] = -np.inf
        X.iloc[2, 2] = np.nan
        y.iloc[3] = np.inf

        clean_X, clean_y = validate_training_matrix(X, y)

        assert len(clean_X) == len(clean_y)
        assert np.isfinite(clean_X.to_numpy(dtype=float)).all()
        assert np.isfinite(clean_y.to_numpy(dtype=float)).all()

    def test_prediction_features_are_filled_and_clipped(self) -> None:
        X = pd.DataFrame({"a": [np.inf], "b": [np.nan], "c": [1e30]})

        clean_X = sanitize_features(X)

        assert np.isfinite(clean_X.to_numpy(dtype=float)).all()
        assert clean_X.loc[0, "a"] == 0.0
        assert clean_X.loc[0, "b"] == 0.0
        assert clean_X.loc[0, "c"] < 1e30
