import os
from typing import cast

import joblib
import numpy as np
import pandas as pd
from ml.base_model import BaseModel
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from ml.base_model import BaseModel


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

    def __init__(self):
        super().__init__("linear")
        self.model = Pipeline([
            ("scaler", StandardScaler()),
            ("lr", LinearRegression()),
        ])

    # ------------------------------------------------------------------ #
    # Training                                                             #
    # ------------------------------------------------------------------ #

    def train(self, X: pd.DataFrame, y: pd.Series) -> None:
        X_arr = X.values if isinstance(X, pd.DataFrame) else X
        y_arr = y.values if isinstance(y, pd.Series) else y

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
        X_arr = X.values if isinstance(X, pd.DataFrame) else X
        return self.model.predict(X_arr)

    # ------------------------------------------------------------------ #
    # Persistence                                                          #
    # ------------------------------------------------------------------ #

    def save(self, path: str) -> None:
        joblib.dump({"model": self.model, "metrics": self.metrics}, path)

    def load(self, path: str) -> bool:
        if not os.path.exists(path):
            return False
        data = joblib.load(path)
        self.model = data["model"]
        self.metrics = data.get("metrics", self.metrics)
        return True

    # ------------------------------------------------------------------ #
    # State check                                                          #
    # ------------------------------------------------------------------ #

    def is_trained(self) -> bool:
        try:
            lr_step = self.model.named_steps.get("lr")
            return lr_step is not None and hasattr(lr_step, "coef_")
        except AttributeError:
            return False