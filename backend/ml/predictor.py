from typing import cast

import pandas as pd
from data.provider import StockDataProvider
from features.engineering import FeatureEngineer
from ml.base_model import BaseModel
from ml.linear_model import LinearRegressionModel
from ml.random_forest_model import RandomForestModel
from schemas import ModelEnum, PredictionResult


class StockPredictor:
    def __init__(self) -> None:
        self.data_provider = StockDataProvider()
        self.feature_engineer = FeatureEngineer()
        self.models: dict[str, BaseModel] = {
            "linear": LinearRegressionModel(),
            "rf": RandomForestModel(),
        }

    def predict(
        self, ticker: str, model_type: ModelEnum, range_key: str = "1y"
    ) -> tuple[PredictionResult, dict[str, float]]:
        df = self.data_provider.get_stock_data(ticker, range_key)
        X, y = self.feature_engineer.prepare_training_data(df)

        model = self.models.get(model_type.value, self.models["linear"])
        model.train(X, y)

        X_pred = self.feature_engineer.prepare_prediction_input(df)
        prediction = model.predict(X_pred)[0]

        result = PredictionResult(
            ticker=ticker,
            model=model_type.value,
            predicted_price=float(prediction),
            confidence=model.get_confidence_score(),
            timestamp=pd.Timestamp.now().isoformat(),
        )

        return result, model.metrics

    def is_trained(self, model_type: str) -> bool:
        return cast(bool, self.models[model_type].is_trained())
