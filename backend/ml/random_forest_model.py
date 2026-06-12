import os

import joblib
import numpy as np
import pandas as pd
from ml.base_model import BaseModel
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split


class RandomForestModel(BaseModel):
    def __init__(self):
        super().__init__("rf")
        self.model = RandomForestRegressor(
            n_estimators=100, max_depth=10, random_state=42, n_jobs=-1
        )

    def train(self, X: pd.DataFrame, y: pd.Series) -> None:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, shuffle=False
        )
        self.model.fit(X_train, y_train)
        y_pred = self.model.predict(X_test)
        self.calculate_metrics(y_test.values, y_pred)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if self.model is None:
            raise ValueError("Model not trained")
        return self.model.predict(X)

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({"model": self.model, "metrics": self.metrics}, path)

    def load(self, path: str) -> bool:
        if os.path.exists(path):
            data = joblib.load(path)
            self.model = data["model"]
            self.metrics = data["metrics"]
            return True
        return False

    def is_trained(self) -> bool:
        return (
            self.model is not None
            and hasattr(self.model, "estimators_")
            and len(self.model.estimators_) > 0
        )
