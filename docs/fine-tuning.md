# Fine-Tuning and Training Pipeline

The project includes a lightweight fine-tuning/training pipeline for Indic finance query intent classification. It uses the project sample corpus rather than external private data.

## Model

- TF-IDF character n-grams (ngram_range=(2, 5)).
- Logistic Regression classifier with balanced class weights.
- Implemented with scikit-learn.

## Dataset

- `data/indic/sample_indic_finance_queries.csv`
- Documented in `data/indic/dataset-card.md`
- **Corpus Size:** 96 rows total, evenly balanced with 12 manually created query examples for each of the 8 intents.
- **Split:** 66% training (63 rows), 34% testing (33 rows).

## Train

```bash
python scripts/validate_indic_dataset.py
python scripts/prepare_indic_dataset.py
python scripts/train_indic_intent_model.py
```

## Evaluate

```bash
python scripts/evaluate_indic_intent_model.py
```

## Runtime Integration

`backend/api/routes.py` calls `backend/ml/indic_intent_model.py` before AI chat. If `models/indic-intent-classifier/model.joblib` exists, the predicted intent is inserted as a system routing hint. If the model is missing, chat behavior is unchanged.

## Limitations

This is a baseline, not a production-grade Indic NLU model. Performance is constrained by the small size of the manually created sample dataset (12 examples per intent across English, Hindi, and Odia). It should be expanded with larger-scale consented/open-licensed data and evaluated per language before stronger claims are made.
