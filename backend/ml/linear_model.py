from typing import cast
import os

import joblib
import numpy as np
import pandas as pd
from ml.base_model import BaseModel
from ml.data_cleaning import sanitize_features, validate_training_matrix
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


class LinearRegressionModel(BaseModel):
    """
    Linear regression wrapped in a StandardScaler pipeline.

    Why scaling matters here:
    - Technical indicators (RSI 0–100, MACD near 0, Volume in millions) live
      on very different scales.  Without scaling, large-magnitude features
      dominate the OLS solution even though they may carry less signal.
    - Scaling is persisted inside the Pipeline so prediction inputs are
      automatically transformed at inference time — no separate scaler state
      to manage.
    """

    def __init__(self) -> None:
        super().__init__("linear")
        self.model = Pipeline(
            [
                ("scaler", StandardScaler()),
                ("lr", LinearRegression()),
            ]
        )

    # ------------------------------------------------------------------ #
    # Training                                                             #
    # ------------------------------------------------------------------ #

    def train(self, X: pd.DataFrame, y: pd.Series) -> None:
        X_clean, y_clean = validate_training_matrix(X, y)
        X_arr = X_clean.values
        y_arr = y_clean.values

        X_train, X_test, y_train, y_test = train_test_split(
            X_arr, y_arr, test_size=0.2, shuffle=False
        )
        self.model.fit(X_train, y_train)
        y_pred = self.model.predict(X_test)
        self.calculate_metrics(y_test, y_pred, mean_price=float(np.mean(y_arr)))

    # ------------------------------------------------------------------ #
    # Inference                                                            #
    # ------------------------------------------------------------------ #

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_trained():
            raise ValueError("LinearRegressionModel has not been trained yet.")
        X_arr = sanitize_features(X).values
        return cast(np.ndarray, self.model.predict(X_arr))

    # ------------------------------------------------------------------ #
    # Persistence                                                          #
    # ------------------------------------------------------------------ #

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({"model": self.model, "metrics": self.metrics}, path)

    def load(self, path: str) -> bool:
        if not os.path.exists(path):
            return False
        data = joblib.load(path)
        loaded_model = data["model"]
        # Backward compat: older versions saved bare LinearRegression
        # without the Pipeline wrapper. Re-wrap so is_trained() works.
        if not hasattr(loaded_model, "named_steps"):
            self.model = Pipeline(
                [
                    ("scaler", StandardScaler()),
                    ("lr", loaded_model),
                ]
            )
        else:
            self.model = loaded_model
        self.metrics = data.get("metrics", self.metrics)
        return True

    # ------------------------------------------------------------------ #
    # State check                                                          #
    # ------------------------------------------------------------------ #

    def is_trained(self) -> bool:
        try:
            if hasattr(self.model, "named_steps"):
                lr_step = self.model.named_steps.get("lr")
                return lr_step is not None and hasattr(lr_step, "coef_")
            return hasattr(self.model, "coef_")
        except AttributeError:
            return False
