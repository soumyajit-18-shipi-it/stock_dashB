"""Prepare the Indic finance query dataset as JSONL for ML experiments."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from validate_indic_dataset import DEFAULT_DATASET, validate_dataset


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data" / "indic" / "prepared_indic_finance_queries.jsonl"


def prepare_dataset(
    dataset_path: Path = DEFAULT_DATASET, output_path: Path = DEFAULT_OUTPUT
) -> Path:
    errors = validate_dataset(dataset_path)
    if errors:
        raise ValueError("Dataset validation failed: " + "; ".join(errors))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with (
        dataset_path.open("r", encoding="utf-8-sig", newline="") as source,
        output_path.open("w", encoding="utf-8", newline="\n") as target,
    ):
        reader = csv.DictReader(source)
        for row in reader:
            text = f"{row['language']} {row['normalized_query']}".strip()
            payload = {
                "id": row["id"],
                "text": text,
                "query_text": row["query_text"],
                "language": row["language"],
                "script": row["script"],
                "intent": row["intent"],
                "related_ticker": row["related_ticker"],
                "expected_response_type": row["expected_response_type"],
            }
            target.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = prepare_dataset(args.dataset, args.output)
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
