"""Train the Indic finance intent classifier."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_indic_dataset import DEFAULT_DATASET, validate_dataset  # noqa: E402

DEFAULT_MODEL_DIR = ROOT / "models" / "indic-intent-classifier"
DEFAULT_REPORT_DIR = ROOT / "reports" / "model-evaluation"


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


def train(dataset_path: Path, model_dir: Path, report_dir: Path) -> dict[str, object]:
    errors = validate_dataset(dataset_path)
    if errors:
        raise ValueError("Dataset validation failed: " + "; ".join(errors))

    texts, labels, _languages = load_rows(dataset_path)
    x_train, x_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.34, random_state=42, stratify=labels
    )

    pipeline = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=1),
            ),
            (
                "classifier",
                LogisticRegression(
                    max_iter=1000, class_weight="balanced", random_state=42
                ),
            ),
        ]
    )
    pipeline.fit(x_train, y_train)
    y_pred = pipeline.predict(x_test)

    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    metadata = {
        "dataset": str(dataset_path.relative_to(ROOT)),
        "training_rows": len(x_train),
        "test_rows": len(x_test),
        "split": "train_test_split(test_size=0.34, random_state=42, stratify=intent)",
        "model_type": "TF-IDF char n-grams + LogisticRegression",
        "created_by": "scripts/train_indic_intent_model.py",
    }

    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {"pipeline": pipeline, "metadata": metadata}, model_dir / "model.joblib"
    )
    (model_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )

    report_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = report_dir / "indic_intent_metrics.json"
    metrics_path.write_text(
        json.dumps({"metadata": metadata, "classification_report": report}, indent=2),
        encoding="utf-8",
    )
    return {"metadata": metadata, "classification_report": report}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    args = parser.parse_args()
    result = train(args.dataset, args.model_dir, args.report_dir)
    print(json.dumps(result["metadata"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
