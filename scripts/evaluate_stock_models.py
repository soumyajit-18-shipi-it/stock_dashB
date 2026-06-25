"""Evaluate stock prediction models on configured ticker/range pairs.

This script uses the existing backend predictor and public market data providers.
It requires network access to Yahoo Finance/Finnhub unless matching data is cached.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import mean
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from schemas import ModelEnum  # noqa: E402
from ml.predictor import StockPredictor  # noqa: E402

DEFAULT_OUTPUT = ROOT / "reports" / "model-evaluation" / "stock_metrics.json"


def evaluate(
    tickers: list[str], range_key: str, output_path: Path
) -> dict[str, object]:
    predictor = StockPredictor()
    rows: list[dict[str, object]] = []
    errors: dict[str, dict[str, str]] = {}

    for ticker in tickers:
        for model in (ModelEnum.LINEAR, ModelEnum.RANDOM_FOREST):
            key = f"{ticker}:{model.value}"
            try:
                result, metrics = predictor.predict(
                    ticker=ticker, model_type=model, range_key=range_key
                )
                rows.append(
                    {
                        "ticker": ticker,
                        "range": range_key,
                        "model": model.value,
                        "predicted_price": result.predicted_price,
                        "trend": result.trend.value,
                        "confidence": result.confidence,
                        "rmse": metrics.rmse,
                        "mae": metrics.mae,
                        "r2": metrics.r2,
                        "mape": None,
                        "note": "MAPE is null because the next-day actual is not known at prediction time in this smoke evaluation.",
                    }
                )
                print(
                    f"OK {ticker} {model.value}: predicted={result.predicted_price} rmse={metrics.rmse:.4f}"
                )
            except Exception as exc:  # noqa: BLE001 - report should capture per-ticker failures
                errors[key] = {
                    "error": str(exc),
                    "exception_type": exc.__class__.__name__,
                    "traceback": traceback.format_exc(limit=6),
                }
                print(f"ERROR {ticker} {model.value}: {exc}")

    numeric = {
        "rmse_mean": mean([float(row["rmse"]) for row in rows]) if rows else None,
        "mae_mean": mean([float(row["mae"]) for row in rows]) if rows else None,
        "r2_mean": mean([float(row["r2"]) for row in rows]) if rows else None,
    }
    report: dict[str, object] = {
        "method": "Existing StockPredictor train/test split metrics per ticker and model.",
        "range": range_key,
        "tickers": tickers,
        "summary": numeric,
        "results": rows,
        "errors": errors,
        "limitations": [
            "This is not a full walk-forward backtest.",
            "Metrics are generated during each model training run from the existing 80/20 chronological split.",
            "Fresh results require network access to public market data providers.",
        ],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tickers", nargs="+", default=["AAPL", "MSFT", "RELIANCE.NS"])
    parser.add_argument("--range", dest="range_key", default="1y")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = evaluate(args.tickers, args.range_key, args.output)
    print(json.dumps(report["summary"], indent=2))
    print(f"Saved {args.output}")
    if report["results"]:
        return 0
    print("All stock model evaluations failed.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
