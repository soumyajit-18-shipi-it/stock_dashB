import os
from typing import cast

import joblib
import numpy as np
import pandas as pd
from ml.base_model import BaseModel
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split


class RandomForestModel(BaseModel):
    """
    Random Forest regressor tuned for financial time-series.

    Key hyperparameter choices:
    - n_estimators=200   : more trees → lower variance; marginal cost on modern CPUs
    - max_depth=8        : shallower than default prevents over-fitting on 1y of daily data
                           (~250 rows); the original depth=10 was borderline for that size.
    - min_samples_leaf=5 : each leaf must represent ≥5 trading days — smooths noise.
    - max_features='sqrt': standard for regression RF; reduces correlation among trees.
    - bootstrap=True     : ensures out-of-bag diversity.

    Feature importance is stored after training so callers can inspect
    which indicators drove the prediction.
    """

    def __init__(self):
        super().__init__("random_forest")
        self.model = RandomForestRegressor(
            n_estimators=200,
            max_depth=8,
            min_samples_leaf=5,
            max_features="sqrt",
            bootstrap=True,
            random_state=42,
            n_jobs=-1,
        )
        self.feature_importances_: dict = {}
        self.feature_names_: list = []

    # ------------------------------------------------------------------ #
    # Training                                                             #
    # ------------------------------------------------------------------ #

    def train(self, X: pd.DataFrame, y: pd.Series) -> None:
        self.feature_names_ = list(X.columns) if isinstance(X, pd.DataFrame) else []
        X_arr = X.values if isinstance(X, pd.DataFrame) else X
        y_arr = y.values if isinstance(y, pd.Series) else y

        X_train, X_test, y_train, y_test = train_test_split(
            X_arr, y_arr, test_size=0.2, shuffle=False
        )
        self.model.fit(X_train, y_train)
        y_pred = self.model.predict(X_test)
        self.calculate_metrics(y_test, y_pred, mean_price=float(np.mean(y_arr)))
        self._capture_feature_importances()

    def _capture_feature_importances(self) -> None:
        if not self.feature_names_:
            return
        importances = self.model.feature_importances_
        paired = zip(self.feature_names_, importances)
        self.feature_importances_ = {
            k: round(float(v), 6)
            for k, v in sorted(paired, key=lambda x: x[1], reverse=True)
        }

    def get_top_features(self, n: int = 5) -> dict:
        """Return the n most important features and their importance scores."""
        items = list(self.feature_importances_.items())
        return dict(items[:n])

    # ------------------------------------------------------------------ #
    # Inference                                                            #
    # ------------------------------------------------------------------ #

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_trained():
            raise ValueError("RandomForestModel has not been trained yet.")
        X_arr = X.values if isinstance(X, pd.DataFrame) else X
        return self.model.predict(X_arr)

    def predict_interval(
        self, X: pd.DataFrame, percentiles: tuple = (10, 90)
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Return a prediction interval from individual tree outputs.

        This is a cheap alternative to formal conformal prediction —
        useful for surfacing uncertainty in the UI without extra deps.

        Returns
        -------
        lower, upper : arrays of shape (n_samples,)
        """
        if not self.is_trained():
            raise ValueError("RandomForestModel has not been trained yet.")
        X_arr = X.values if isinstance(X, pd.DataFrame) else X
        tree_preds = np.array([t.predict(X_arr) for t in self.model.estimators_])
        lower = np.percentile(tree_preds, percentiles[0], axis=0)
        upper = np.percentile(tree_preds, percentiles[1], axis=0)
        return lower, upper

    # ------------------------------------------------------------------ #
    # Persistence                                                          #
    # ------------------------------------------------------------------ #

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(
            {
                "model": self.model,
                "metrics": self.metrics,
                "feature_importances": self.feature_importances_,
                "feature_names": self.feature_names_,
            },
            path,
        )

    def load(self, path: str) -> bool:
        if not os.path.exists(path):
            return False
        data = joblib.load(path)
        self.model = data["model"]
        self.metrics = data.get("metrics", self.metrics)
        self.feature_importances_ = data.get("feature_importances", {})
        self.feature_names_ = data.get("feature_names", [])
        return True

    # ------------------------------------------------------------------ #
    # State check                                                          #
    # ------------------------------------------------------------------ #

    def is_trained(self) -> bool:
        return (
            self.model is not None
            and hasattr(self.model, "estimators_")
            and len(self.model.estimators_) > 0
        )
