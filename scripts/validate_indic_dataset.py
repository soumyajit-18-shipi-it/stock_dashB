"""Validate the Indic finance query dataset."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / "data" / "indic" / "sample_indic_finance_queries.csv"
DEFAULT_SCHEMA = ROOT / "data" / "indic" / "schema.json"


def load_schema(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_dataset(
    dataset_path: Path = DEFAULT_DATASET, schema_path: Path = DEFAULT_SCHEMA
) -> list[str]:
    schema = load_schema(schema_path)
    required = list(schema["required"])  # type: ignore[index]
    properties = schema["properties"]  # type: ignore[index]
    allowed_languages = set(properties["language"]["enum"])  # type: ignore[index]
    allowed_intents = set(properties["intent"]["enum"])  # type: ignore[index]

    errors: list[str] = []
    seen_ids: set[str] = set()
    seen_queries: set[tuple[str, str]] = set()

    with dataset_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            return ["dataset has no header row"]

        missing_columns = [
            column for column in required if column not in reader.fieldnames
        ]
        if missing_columns:
            errors.append(f"missing required columns: {', '.join(missing_columns)}")

        for line_number, row in enumerate(reader, start=2):
            for column in required:
                if row.get(column) is None:
                    continue
                if column != "related_ticker" and row[column].strip() == "":
                    errors.append(
                        f"line {line_number}: empty required value for {column}"
                    )

            row_id = row.get("id", "").strip()
            if row_id in seen_ids:
                errors.append(f"line {line_number}: duplicate id {row_id}")
            seen_ids.add(row_id)

            language = row.get("language", "").strip()
            if language not in allowed_languages:
                errors.append(f"line {line_number}: unsupported language {language}")

            intent = row.get("intent", "").strip()
            if intent not in allowed_intents:
                errors.append(f"line {line_number}: unsupported intent {intent}")

            consent = row.get("consent_status", "").strip()
            license_name = row.get("license", "").strip()
            if not consent:
                errors.append(f"line {line_number}: missing consent_status")
            if not license_name:
                errors.append(f"line {line_number}: missing license")

            query_key = (language, row.get("normalized_query", "").strip().casefold())
            if query_key in seen_queries:
                errors.append(
                    f"line {line_number}: duplicate normalized query for {language}"
                )
            seen_queries.add(query_key)

            query_text = row.get("query_text", "")
            try:
                query_text.encode("utf-8").decode("utf-8")
            except UnicodeError:
                errors.append(f"line {line_number}: query_text is not valid UTF-8")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args()

    errors = validate_dataset(args.dataset, args.schema)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"OK: {args.dataset} passed validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
