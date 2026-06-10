import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from ml.linear_model import LinearRegressionModel
from ml.random_forest_model import RandomForestModel
from features.engineering import FeatureEngineer


class TestMLModels:
    def setup_method(self):
        np.random.seed(42)
        n = 200
        self.df = pd.DataFrame({
            "Close": 100 + np.cumsum(np.random.randn(n) * 2),
            "Volume": 1000000 + np.random.randint(-100000, 100000, n)
        })
        self.engineer = FeatureEngineer()
        self.X, self.y = self.engineer.prepare_training_data(self.df)
        self.temp_dir = tempfile.mkdtemp()

    def test_linear_regression_train(self):
        model = LinearRegressionModel()
        model.train(self.X, self.y)
        assert model.is_trained()
        assert "rmse" in model.metrics
        assert "mae" in model.metrics
        assert "r2" in model.metrics

    def test_linear_regression_predict(self):
        model = LinearRegressionModel()
        model.train(self.X, self.y)
        X_pred = self.engineer.prepare_prediction_input(self.df)
        prediction = model.predict(X_pred)
        assert len(prediction) == 1
        assert isinstance(prediction[0], (int, float))

    def test_linear_regression_save_load(self):
        model = LinearRegressionModel()
        model.train(self.X, self.y)
        path = os.path.join(self.temp_dir, "linear_test.pkl")
        model.save(path)
        assert os.path.exists(path)

        new_model = LinearRegressionModel()
        loaded = new_model.load(path)
        assert loaded
        assert new_model.is_trained()

    def test_random_forest_train(self):
        model = RandomForestModel()
        model.train(self.X, self.y)
        assert model.is_trained()
        assert "rmse" in model.metrics
        assert "mae" in model.metrics
        assert "r2" in model.metrics

    def test_random_forest_predict(self):
        model = RandomForestModel()
        model.train(self.X, self.y)
        X_pred = self.engineer.prepare_prediction_input(self.df)
        prediction = model.predict(X_pred)
        assert len(prediction) == 1
        assert isinstance(prediction[0], (int, float))

    def test_random_forest_save_load(self):
        model = RandomForestModel()
        model.train(self.X, self.y)
        path = os.path.join(self.temp_dir, "rf_test.pkl")
        model.save(path)
        assert os.path.exists(path)

        new_model = RandomForestModel()
        loaded = new_model.load(path)
        assert loaded
        assert new_model.is_trained()

    def test_confidence_score(self):
        model = LinearRegressionModel()
        model.train(self.X, self.y)
        confidence = model.get_confidence_score()
        assert 0 <= confidence <= 1
