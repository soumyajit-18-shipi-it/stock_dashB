import os
from typing import Dict, Tuple, Optional
import pandas as pd
import numpy as np
from ..data.provider import StockDataProvider
from ..features.engineering import FeatureEngineer
from .base_model import BaseModel
from .linear_model import LinearRegressionModel
from .random_forest_model import RandomForestModel
from ..schemas import ModelEnum, TrendDirection, PredictionResult, ModelMetrics


class StockPredictor:
    MODEL_DIR = "models"
    MODEL_FILES = {
        ModelEnum.LINEAR: "linear.pkl",
        ModelEnum.RANDOM_FOREST: "random_forest.pkl",
    }

    def __init__(self):
        self.data_provider = StockDataProvider()
        self.feature_engineer = FeatureEngineer()
        self.models: Dict[str, BaseModel] = {
            ModelEnum.LINEAR.value: LinearRegressionModel(),
            ModelEnum.RANDOM_FOREST.value: RandomForestModel(),
        }
        self._ensure_model_dir()

    def _ensure_model_dir(self) -> None:
        os.makedirs(self.MODEL_DIR, exist_ok=True)

    def _get_model_path(self, model_type: ModelEnum) -> str:
        filename = self.MODEL_FILES.get(model_type, "linear.pkl")
        return os.path.join(self.MODEL_DIR, filename)

    def _load_model(self, model_type: ModelEnum) -> bool:
        model = self.models.get(model_type.value)
        if model:
            path = self._get_model_path(model_type)
            return model.load(path)
        return False

    def _train_model(self, model_type: ModelEnum, df: pd.DataFrame) -> None:
        model = self.models.get(model_type.value)
        if model:
            X, y = self.feature_engineer.prepare_training_data(df)
            model.train(X, y)
            path = self._get_model_path(model_type)
            model.save(path)

    def get_or_train_model(self, model_type: ModelEnum, df: pd.DataFrame) -> BaseModel:
        model = self.models.get(model_type.value)
        if not model:
            raise ValueError(f"Unknown model type: {model_type}")

        if not self._load_model(model_type):
            self._train_model(model_type, df)
            self._load_model(model_type)

        model = self.models.get(model_type.value)
        if not model or not model.is_trained():
            self._train_model(model_type, df)

        return self.models[model_type.value]

    def predict(
        self,
        ticker: str,
        model_type: ModelEnum = ModelEnum.LINEAR,
        range_key: str = "1y"
    ) -> Tuple[PredictionResult, ModelMetrics]:
        df = self.data_provider.get_stock_data(ticker, range_key)

        model = self.get_or_train_model(model_type, df)

        X_pred = self.feature_engineer.prepare_prediction_input(df)
        prediction = model.predict(X_pred)
        predicted_price = float(prediction[0])

        last_close = df["Close"].iloc[-1]
        trend = TrendDirection.INCREASE if predicted_price > last_close else TrendDirection.DECREASE
        confidence = model.get_confidence_score()

        result = PredictionResult(
            predicted_price=round(predicted_price, 4),
            trend=trend,
            confidence=round(confidence, 4),
            model_used=model_type.value
        )

        metrics = ModelMetrics(**model.metrics)

        return result, metrics
