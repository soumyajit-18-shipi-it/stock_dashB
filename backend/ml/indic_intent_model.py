"""Lightweight Indic finance query intent classifier."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_PATH = ROOT / "models" / "indic-intent-classifier" / "model.joblib"


@dataclass(frozen=True)
class IndicIntentPrediction:
    intent: str
    confidence: float
    language: str | None = None


class IndicIntentClassifier:
    """Loads a trained scikit-learn text classifier when available."""

    def __init__(self, model_path: Path = DEFAULT_MODEL_PATH) -> None:
        self.model_path = model_path
        self._pipeline: Any | None = None
        self._metadata: dict[str, Any] = {}

    def is_available(self) -> bool:
        return self.model_path.exists()

    def load(self) -> bool:
        if self._pipeline is not None:
            return True
        if not self.model_path.exists():
            return False
        payload = joblib.load(self.model_path)
        self._pipeline = payload["pipeline"]
        self._metadata = payload.get("metadata", {})
        return True

    def predict(
        self, text: str, language: str | None = None
    ) -> IndicIntentPrediction | None:
        if not text.strip() or not self.load() or self._pipeline is None:
            return None

        model_input = f"{language or ''} {text}".strip()
        intent = str(self._pipeline.predict([model_input])[0])
        confidence = 0.0
        if hasattr(self._pipeline, "predict_proba"):
            probabilities = self._pipeline.predict_proba([model_input])[0]
            confidence = float(max(probabilities))
        return IndicIntentPrediction(
            intent=intent, confidence=round(confidence, 4), language=language
        )


_classifier = IndicIntentClassifier()


def get_indic_intent_classifier() -> IndicIntentClassifier:
    return _classifier
