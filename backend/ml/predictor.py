"""
predictor.py
------------
Orchestrates data fetching, model management, and prediction — with
two key additions for `stock_dashB`:

1. **Ensemble arbitration** (see ml/ensemble.py):
   Runs both Linear and RF models and resolves disagreements by
   picking the more confident prediction.

2. **Indian market awareness**:
   NSE/BSE trading hours are 09:15–15:30 IST (UTC+5:30).
   Cached `.pkl` model files are considered stale if they are older
   than one full market session, so predictions always reflect the
   most recent OHLCV data rather than stale fits.

   Market session staleness rules:
   - Before 09:15 IST today  → use yesterday's session close data
   - After  15:30 IST today  → today's session is complete; retrain if
     the pkl was last written before today 15:30 IST
   - Between 09:15–15:30 IST → market is live; use previous close data
     (intraday data quality for prediction is lower)
"""

import os
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Tuple, Optional

import pandas as pd
import numpy as np

from data.provider import StockDataProvider
from features.engineering import FeatureEngineer
from ml.base_model import BaseModel
from ml.linear_model import LinearRegressionModel
from ml.random_forest_model import RandomForestModel
from ml.ensemble import arbitrate, EnsembleResult
from schemas import ModelEnum, TrendDirection, PredictionResult, ModelMetrics


# IST = UTC + 5:30
IST = timezone(timedelta(hours=5, minutes=30))

# NSE/BSE session boundaries in IST
_NSE_OPEN  = (9, 15)   # 09:15
_NSE_CLOSE = (15, 30)  # 15:30


def _ist_now() -> datetime:
    return datetime.now(IST)


def _session_close_today() -> datetime:
    """Return today's NSE session close timestamp in IST."""
    n = _ist_now()
    return n.replace(hour=_NSE_CLOSE[0], minute=_NSE_CLOSE[1], second=0, microsecond=0)


def _model_is_stale(path: str) -> bool:
    """
    Return True when the saved model pkl should be retrained.

    Logic:
    - If the file doesn't exist → stale (needs training).
    - If today's NSE session has ended and the file was written before
      that close → stale (new data available).
    - Otherwise → fresh.
    """
    if not os.path.exists(path):
        return True

    mtime = datetime.fromtimestamp(os.path.getmtime(path), tz=IST)
    now = _ist_now()
    session_close = _session_close_today()

    # Session has ended today and model was written before that close
    if now >= session_close and mtime < session_close:
        return True

    return False


class StockPredictor:
    MODEL_DIR = "models"
    MODEL_FILES = {
        ModelEnum.LINEAR:        "linear.pkl",
        ModelEnum.RANDOM_FOREST: "random_forest.pkl",
    }

    def __init__(self):
        self.data_provider  = StockDataProvider()
        self.feature_engineer = FeatureEngineer()
        self.models: Dict[str, BaseModel] = {
            ModelEnum.LINEAR.value:        LinearRegressionModel(),
            ModelEnum.RANDOM_FOREST.value: RandomForestModel(),
        }
        self._ensure_model_dir()

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    def _ensure_model_dir(self) -> None:
        os.makedirs(self.MODEL_DIR, exist_ok=True)

    def _get_model_path(self, model_type: ModelEnum) -> str:
        filename = self.MODEL_FILES.get(model_type, "linear.pkl")
        return os.path.join(self.MODEL_DIR, filename)

    def _load_model(self, model_type: ModelEnum) -> bool:
        model = self.models.get(model_type.value)
        if model:
            return model.load(self._get_model_path(model_type))
        return False

    def _train_model(self, model_type: ModelEnum, df: pd.DataFrame) -> None:
        model = self.models.get(model_type.value)
        if model:
            X, y = self.feature_engineer.prepare_training_data(df)
            model.train(X, y)
            model.save(self._get_model_path(model_type))

    def _get_or_train(self, model_type: ModelEnum, df: pd.DataFrame) -> BaseModel:
        """
        Load model from disk unless it is stale; train from scratch if needed.
        """
        path = self._get_model_path(model_type)
        model = self.models[model_type.value]

        if _model_is_stale(path):
            self._train_model(model_type, df)
            self._load_model(model_type)
        else:
            loaded = self._load_model(model_type)
            if not loaded or not model.is_trained():
                self._train_model(model_type, df)
                self._load_model(model_type)

        return self.models[model_type.value]

    # ------------------------------------------------------------------ #
    # Public API — single-model prediction                                 #
    # ------------------------------------------------------------------ #

    def predict(
        self,
        ticker: str,
        model_type: ModelEnum = ModelEnum.LINEAR,
        range_key: str = "1y",
    ) -> Tuple[PredictionResult, ModelMetrics]:
        """
        Run a single model and return its prediction.

        For production use, prefer `predict_ensemble` which combines
        both models and resolves disagreements automatically.
        """
        df = self.data_provider.get_stock_data(ticker, range_key)
        model = self._get_or_train(model_type, df)

        X_pred = self.feature_engineer.prepare_prediction_input(df)
        predicted_price = float(model.predict(X_pred)[0])
        last_close = float(df["Close"].iloc[-1])

        trend = (
            TrendDirection.INCREASE
            if predicted_price > last_close
            else TrendDirection.DECREASE
        )

        result = PredictionResult(
            predicted_price=round(predicted_price, 4),
            trend=trend,
            confidence=round(model.get_confidence_score(), 4),
            model_used=model_type.value,
        )
        return result, ModelMetrics(**{
            k: v for k, v in model.metrics.items()
            if k in ("rmse", "mae", "r2")
        })

    # ------------------------------------------------------------------ #
    # Public API — ensemble prediction (recommended)                      #
    # ------------------------------------------------------------------ #

    def predict_ensemble(
        self,
        ticker: str,
        range_key: str = "1y",
    ) -> Tuple[PredictionResult, ModelMetrics, EnsembleResult]:
        """
        Run both models, arbitrate disagreements, and return a single
        best prediction along with full ensemble metadata.

        Returns
        -------
        result          : PredictionResult — the final price / trend / confidence
        metrics         : ModelMetrics of the winning model
        ensemble_detail : EnsembleResult with per-model breakdown and
                          arbitration_reason string (suitable for UI tooltip)
        """
        df = self.data_provider.get_stock_data(ticker, range_key)

        lin_model = self._get_or_train(ModelEnum.LINEAR, df)
        rf_model  = self._get_or_train(ModelEnum.RANDOM_FOREST, df)

        X_pred = self.feature_engineer.prepare_prediction_input(df)

        lin_price = float(lin_model.predict(X_pred)[0])
        rf_price  = float(rf_model.predict(X_pred)[0])
        lin_conf  = lin_model.get_confidence_score()
        rf_conf   = rf_model.get_confidence_score()
        last_close = float(df["Close"].iloc[-1])

        ensemble = arbitrate(
            linear_price=lin_price,
            rf_price=rf_price,
            linear_confidence=lin_conf,
            rf_confidence=rf_conf,
            last_close=last_close,
        )

        trend = (
            TrendDirection.INCREASE
            if ensemble.predicted_price > last_close
            else TrendDirection.DECREASE
        )

        # Fetch metrics from the winning model
        winning_model = (
            lin_model
            if ensemble.model_used == "linear"
            else rf_model
        )
        # When blended, use the higher-confidence model's metrics
        if ensemble.model_used == "ensemble":
            winning_model = lin_model if lin_conf >= rf_conf else rf_model

        result = PredictionResult(
            predicted_price=ensemble.predicted_price,
            trend=trend,
            confidence=ensemble.confidence,
            model_used=ensemble.model_used,
        )

        metrics = ModelMetrics(**{
            k: v for k, v in winning_model.metrics.items()
            if k in ("rmse", "mae", "r2")
        })

        return result, metrics, ensemble

    # ------------------------------------------------------------------ #
    # Utility                                                              #
    # ------------------------------------------------------------------ #

    def force_retrain(self, ticker: str, range_key: str = "1y") -> None:
        """Unconditionally retrain both models for a given ticker."""
        df = self.data_provider.get_stock_data(ticker, range_key)
        self._train_model(ModelEnum.LINEAR, df)
        self._train_model(ModelEnum.RANDOM_FOREST, df)

    def is_market_open(self) -> bool:
        """Return True if NSE/BSE is currently in session (IST, weekdays only)."""
        now = _ist_now()
        if now.weekday() >= 5:   # Saturday=5, Sunday=6
            return False
        open_time  = now.replace(hour=_NSE_OPEN[0],  minute=_NSE_OPEN[1],  second=0, microsecond=0)
        close_time = now.replace(hour=_NSE_CLOSE[0], minute=_NSE_CLOSE[1], second=0, microsecond=0)
        return open_time <= now <= close_time