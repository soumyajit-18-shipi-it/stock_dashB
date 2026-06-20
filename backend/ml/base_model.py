from abc import ABC, abstractmethod
from typing import Optional, Any, Dict
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


class BaseModel(ABC):
    """
    Abstract base for all stock prediction models.

    Confidence scoring uses a blended formula:
        raw_r2_component  = (r2 + 1) / 2          # maps [-1, 1] → [0, 1]
        rmse_penalty      = rmse / (mean_price + ε) # relative error
        confidence        = raw_r2_component * (1 - min(rmse_penalty, 0.5))

    This prevents a model with a high R² but huge absolute RMSE from
    appearing artificially confident — important for Indian mid/small-cap
    stocks that can have wide intraday ranges.
    """

    def __init__(self, name: str):
        self.name = name
        self.model: Any = None
        self.metrics: Dict[str, Any] = {
            "rmse": 0.0,
            "mae": 0.0,
            "r2": 0.0,
            "mean_price": 1.0,
        }

    # ------------------------------------------------------------------ #
    # Abstract interface                                                   #
    # ------------------------------------------------------------------ #

    @abstractmethod
    def train(self, X: pd.DataFrame, y: pd.Series) -> None:
        pass

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        pass

    @abstractmethod
    def save(self, path: str) -> None:
        pass

    @abstractmethod
    def load(self, path: str) -> bool:
        pass

    @abstractmethod
    def is_trained(self) -> bool:
        pass

    # ------------------------------------------------------------------ #
    # Shared helpers                                                       #
    # ------------------------------------------------------------------ #

    def calculate_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        mean_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Compute RMSE / MAE / R² and store them.

        Parameters
        ----------
        y_true, y_pred : arrays of actuals and predictions
        mean_price     : average closing price over the training window;
                         used to compute a relative RMSE penalty.
                         Falls back to mean(y_true) when not supplied.
        """
        rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
        mae = float(mean_absolute_error(y_true, y_pred))
        r2 = float(r2_score(y_true, y_pred))
        mp = float(mean_price) if mean_price is not None else float(np.mean(y_true))

        self.metrics = {
            "rmse": rmse,
            "mae": mae,
            "r2": r2,
            "mean_price": mp,
        }
        return self.metrics

    def get_confidence_score(self) -> float:
        """
        Blended confidence ∈ [0, 1].

        A model that fits well (high R²) but has large absolute errors
        relative to the stock price will be penalised so the ensemble
        arbitrator can prefer the model that is actually more reliable.
        """
        r2 = float(self.metrics.get("r2", 0.0) or 0.0)
        rmse = float(self.metrics.get("rmse", 0.0) or 0.0)
        mean_price = float(self.metrics.get("mean_price", 1.0) or 1.0)  # guard /0

        r2_component = (r2 + 1) / 2  # [0, 1]
        relative_rmse = rmse / mean_price  # dimensionless
        rmse_penalty = min(relative_rmse, 0.5)  # cap at 0.5

        score = r2_component * (1.0 - rmse_penalty)
        return float(round(max(0.0, min(1.0, score)), 6))
