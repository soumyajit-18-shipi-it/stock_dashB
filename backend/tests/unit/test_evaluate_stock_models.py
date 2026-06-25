from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

import evaluate_stock_models  # noqa: E402


class FakePredictor:
    def predict(self, ticker, model_type, range_key):  # noqa: ANN001, ANN201
        if ticker == "BAD":
            raise ValueError("synthetic ticker failure")
        result = SimpleNamespace(
            predicted_price=101.25,
            trend=SimpleNamespace(value="increase"),
            confidence=0.75,
        )
        metrics = SimpleNamespace(rmse=1.0, mae=0.5, r2=0.8)
        return result, metrics


def test_stock_evaluation_records_errors_and_continues(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(evaluate_stock_models, "StockPredictor", FakePredictor)
    output_path = tmp_path / "stock_metrics.json"

    report = evaluate_stock_models.evaluate(["GOOD", "BAD"], "1y", output_path)

    assert output_path.exists()
    saved = json.loads(output_path.read_text(encoding="utf-8"))
    assert len(report["results"]) == 2
    assert len(saved["results"]) == 2
    assert "BAD:linear" in saved["errors"]
    assert "BAD:rf" in saved["errors"]
