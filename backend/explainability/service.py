"""Local additive explanations for persisted stock prediction models."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd

from data.provider import StockDataProvider
from ml.data_cleaning import sanitize_features
from ml.linear_model import LinearRegressionModel
from ml.predictor import StockPredictor
from ml.random_forest_model import RandomForestModel
from schemas import DateRangeEnum, ModelEnum

logger = logging.getLogger("stock_dashboard")


FEATURE_LABELS = {
    "Close": "Current close",
    "Volume": "Trading volume",
    "ma7": "7-day moving average",
    "ma21": "21-day moving average",
    "returns": "Daily return",
    "lag1": "Price lag 1 day",
    "lag2": "Price lag 2 days",
    "lag3": "Price lag 3 days",
    "lag4": "Price lag 4 days",
    "lag5": "Price lag 5 days",
    "volume_change": "Volume change",
}


@dataclass(frozen=True)
class ExplanationFeature:
    feature: str
    display_name: str
    value: float
    contribution: float
    direction: str
    importance_percent: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExplanationResult:
    ticker: str
    model: str
    method: str
    provider_status: str
    base_value: float
    predicted_price: float
    current_price: float
    expected_return: float
    confidence: float
    uncertainty_lower: float
    uncertainty_upper: float
    features: tuple[ExplanationFeature, ...]
    additivity_residual: float

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["features"] = [item.to_dict() for item in self.features]
        return data


class PredictionExplanationService:
    """Select a mathematically appropriate local explainer per model family."""

    def __init__(
        self,
        predictor: StockPredictor | None = None,
        data_provider: StockDataProvider | None = None,
    ) -> None:
        self.predictor = predictor or StockPredictor()
        self.data_provider = data_provider or StockDataProvider()
        self.background_rows = 64
        self.linear_interval_z = 1.281552

    def explain(
        self,
        ticker: str,
        range_key: DateRangeEnum = DateRangeEnum.ONE_YEAR,
        model_type: ModelEnum = ModelEnum.RANDOM_FOREST,
        data: pd.DataFrame | None = None,
    ) -> ExplanationResult:
        symbol = ticker.strip().upper()
        fetch_range = "1y" if range_key == DateRangeEnum.ONE_MONTH else range_key.value
        history = (
            data
            if data is not None
            else self.data_provider.get_stock_data(symbol, fetch_range)
        )
        model, prediction_input, background = (
            self.predictor.prepare_explanation_context(
                symbol,
                model_type,
                range_key.value,
                history,
                self.background_rows,
            )
        )
        prediction_input = sanitize_features(prediction_input)
        background = sanitize_features(background)
        predicted_price = float(model.predict(prediction_input)[0])
        current_price = float(history["Close"].iloc[-1])

        method, status, base_value, contributions = self._explain_model(
            model, prediction_input, background, predicted_price
        )
        additivity_residual = predicted_price - (
            base_value + float(np.sum(contributions))
        )
        features = self._build_features(
            list(prediction_input.columns),
            prediction_input.iloc[0].to_numpy(dtype=float),
            contributions,
        )
        lower, upper = self._uncertainty(
            model, prediction_input, predicted_price
        )
        expected_return = (
            (predicted_price - current_price) / current_price
            if current_price
            else 0.0
        )
        return ExplanationResult(
            ticker=symbol,
            model=model_type.value,
            method=method,
            provider_status=status,
            base_value=round(base_value, 6),
            predicted_price=round(predicted_price, 6),
            current_price=round(current_price, 6),
            expected_return=round(expected_return, 6),
            confidence=round(model.get_confidence_score(), 6),
            uncertainty_lower=round(lower, 6),
            uncertainty_upper=round(upper, 6),
            features=tuple(features),
            additivity_residual=round(additivity_residual, 8),
        )

    def _explain_model(
        self,
        model: Any,
        prediction_input: pd.DataFrame,
        background: pd.DataFrame,
        predicted_price: float,
    ) -> tuple[str, str, float, np.ndarray]:
        try:
            import shap  # pylint: disable=import-outside-toplevel

            if isinstance(model, RandomForestModel):
                explainer = shap.TreeExplainer(
                    model.model,
                    data=background.to_numpy(dtype=float),
                    feature_perturbation="interventional",
                )
                explanation = explainer(
                    prediction_input.to_numpy(dtype=float),
                    check_additivity=False,
                )
                values = np.asarray(explanation.values)[0].astype(float)
                base_value = float(np.asarray(explanation.base_values).reshape(-1)[0])
                return "shap.TreeExplainer", "available", base_value, values
            if isinstance(model, LinearRegressionModel):
                scaler = model.model.named_steps["scaler"]
                regressor = model.model.named_steps["lr"]
                transformed_background = scaler.transform(background.to_numpy(dtype=float))
                transformed_input = scaler.transform(
                    prediction_input.to_numpy(dtype=float)
                )
                explainer = shap.LinearExplainer(
                    regressor, transformed_background
                )
                explanation = explainer(transformed_input)
                values = np.asarray(explanation.values)[0].astype(float)
                base_value = float(np.asarray(explanation.base_values).reshape(-1)[0])
                return "shap.LinearExplainer", "available", base_value, values
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.warning("SHAP explanation degraded to local ablation: %s", exc)

        base_value, contributions = self._local_ablation(
            model, prediction_input, background, predicted_price
        )
        return (
            "local_ablation_fallback",
            "degraded",
            base_value,
            contributions,
        )

    def _local_ablation(
        self,
        model: Any,
        prediction_input: pd.DataFrame,
        background: pd.DataFrame,
        predicted_price: float,
    ) -> tuple[float, np.ndarray]:
        base_value = float(np.mean(model.predict(background)))
        raw = []
        background_mean = background.mean(axis=0)
        for column in prediction_input.columns:
            ablated = prediction_input.copy()
            ablated.loc[:, column] = float(background_mean[column])
            raw.append(predicted_price - float(model.predict(ablated)[0]))
        contributions = np.asarray(raw, dtype=float)
        target_sum = predicted_price - base_value
        current_sum = float(contributions.sum())
        if abs(current_sum) > np.finfo(float).eps:
            contributions *= target_sum / current_sum
        else:
            contributions[:] = target_sum / max(len(contributions), 1)
        return base_value, contributions

    def _uncertainty(
        self,
        model: Any,
        prediction_input: pd.DataFrame,
        predicted_price: float,
    ) -> tuple[float, float]:
        if isinstance(model, RandomForestModel):
            lower, upper = model.predict_interval(
                prediction_input, percentiles=(10, 90)
            )
            return float(lower[0]), float(upper[0])
        rmse = float(model.metrics.get("rmse", 0.0) or 0.0)
        margin = self.linear_interval_z * rmse
        return predicted_price - margin, predicted_price + margin

    def _build_features(
        self,
        names: list[str],
        values: np.ndarray,
        contributions: np.ndarray,
    ) -> list[ExplanationFeature]:
        total = float(np.abs(contributions).sum())
        result = [
            ExplanationFeature(
                feature=name,
                display_name=FEATURE_LABELS.get(name, name.replace("_", " ").title()),
                value=round(float(value), 6),
                contribution=round(float(contribution), 6),
                direction="positive" if contribution >= 0 else "negative",
                importance_percent=round(
                    abs(float(contribution)) / total * 100.0 if total else 0.0,
                    4,
                ),
            )
            for name, value, contribution in zip(names, values, contributions)
        ]
        return sorted(
            result, key=lambda item: item.importance_percent, reverse=True
        )
