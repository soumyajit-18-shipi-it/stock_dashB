"""Evaluate the trained Indic finance intent classifier."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import joblib
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_indic_dataset import DEFAULT_DATASET, validate_dataset  # noqa: E402

DEFAULT_MODEL_PATH = ROOT / "models" / "indic-intent-classifier" / "model.joblib"
DEFAULT_OUTPUT = ROOT / "reports" / "model-evaluation" / "indic_intent_metrics.json"


def load_rows(dataset_path: Path) -> tuple[list[str], list[str], list[str]]:
    texts: list[str] = []
    labels: list[str] = []
    languages: list[str] = []
    with dataset_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            texts.append(f"{row['language']} {row['normalized_query']}")
            labels.append(row["intent"])
            languages.append(row["language"])
    return texts, labels, languages


def evaluate(
    dataset_path: Path, model_path: Path, output_path: Path
) -> dict[str, object]:
    errors = validate_dataset(dataset_path)
    if errors:
        raise ValueError("Dataset validation failed: " + "; ".join(errors))
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model not found: {model_path}. Run scripts/train_indic_intent_model.py first."
        )

    texts, labels, languages = load_rows(dataset_path)
    _x_train, x_test, _y_train, y_test, _lang_train, lang_test = train_test_split(
        texts, labels, languages, test_size=0.34, random_state=42, stratify=labels
    )
    payload = joblib.load(model_path)
    pipeline = payload["pipeline"]
    y_pred = pipeline.predict(x_test)

    language_metrics: dict[str, object] = {}
    for language in sorted(set(lang_test)):
        indexes = [idx for idx, value in enumerate(lang_test) if value == language]
        actual = [y_test[idx] for idx in indexes]
        predicted = [y_pred[idx] for idx in indexes]
        language_metrics[language] = {
            "accuracy": accuracy_score(actual, predicted),
            "macro_f1": f1_score(actual, predicted, average="macro", zero_division=0),
            "samples": len(indexes),
        }

    labels_sorted = sorted(set(labels))
    result: dict[str, object] = {
        "metadata": payload.get("metadata", {}),
        "accuracy": accuracy_score(y_test, y_pred),
        "macro_f1": f1_score(y_test, y_pred, average="macro", zero_division=0),
        "weighted_f1": f1_score(y_test, y_pred, average="weighted", zero_division=0),
        "macro_precision": precision_score(
            y_test, y_pred, average="macro", zero_division=0
        ),
        "macro_recall": recall_score(y_test, y_pred, average="macro", zero_division=0),
        "classification_report": classification_report(
            y_test, y_pred, output_dict=True, zero_division=0
        ),
        "labels": labels_sorted,
        "confusion_matrix": confusion_matrix(
            y_test, y_pred, labels=labels_sorted
        ).tolist(),
        "per_language": language_metrics,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = evaluate(args.dataset, args.model, args.output)
    print(
        json.dumps(
            {k: result[k] for k in ("accuracy", "macro_f1", "weighted_f1")}, indent=2
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
