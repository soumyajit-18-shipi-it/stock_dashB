# Indic Finance Query Dataset

This folder contains a small, project-owned sample corpus for multilingual finance queries. It is designed for intent classification and prompt routing in Stock Intelligence Dashboard.

The dataset is intentionally modest and transparent. It is not a broad benchmark, and it should not be presented as representative of all Indian financial users. It provides real repository evidence for Hindi and Odia finance terminology coverage and a reproducible baseline training pipeline.

## Files

- `sample_indic_finance_queries.csv`: sample query corpus.
- `schema.json`: machine-readable schema for validation.
- `dataset-card.md`: source, license, consent, limits, and ethical notes.

## Languages

Current rows cover:

- English (`en`)
- Hindi (`hi`)
- Odia (`or`)

The schema allows future additions for Bengali, Telugu, Tamil, Marathi, Gujarati, Kannada, Malayalam, Punjabi, and Assamese after consented/open-licensed collection.

## Usage

Validate:

```bash
python scripts/validate_indic_dataset.py
```

Prepare normalized JSONL:

```bash
python scripts/prepare_indic_dataset.py
```

Train the Indic intent classifier:

```bash
python scripts/train_indic_intent_model.py
```
