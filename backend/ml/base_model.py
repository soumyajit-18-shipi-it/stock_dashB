from abc import ABC, abstractmethod
from typing import Tuple, Optional
import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score


class BaseModel(ABC):
    def __init__(self, name: str):
        self.name = name
        self.model = None
        self.metrics = {"rmse": 0.0, "mae": 0.0, "r2": 0.0}

    @abstractmethod
    def train(self, X: pd.DataFrame, y: pd.Series) -> None:
        pass

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        pass

    def calculate_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> dict:
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mae = mean_absolute_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)
        self.metrics = {"rmse": float(rmse), "mae": float(mae), "r2": float(r2)}
        return self.metrics

    def get_confidence_score(self) -> float:
        r2 = self.metrics.get("r2", 0.0)
        return max(0.0, min(1.0, (r2 + 1) / 2))

    @abstractmethod
    def save(self, path: str) -> None:
        pass

    @abstractmethod
    def load(self, path: str) -> bool:
        pass

    @abstractmethod
    def is_trained(self) -> bool:
        pass
