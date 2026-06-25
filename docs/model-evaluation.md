# Model Evaluation

## Stock Models

Script:

```bash
python scripts/evaluate_stock_models.py --tickers AAPL MSFT RELIANCE.NS --range 1y
```

Output:

- `reports/model-evaluation/stock_metrics.json`

Metrics (Mean values for AAPL, MSFT, and RELIANCE.NS):

- **Mean RMSE:** 17.4171
- **Mean MAE:** 14.1429
- **Mean R²:** 0.4025
- MAPE is recorded as `null` in the smoke evaluation because next-day actuals are not known at inference time.

Method:

The script uses the existing `StockPredictor`, which trains each model with a chronological 80/20 split. This is a smoke evaluation, not a walk-forward backtest. Robust fallback loading from local cached `.pkl` files is used if public market API queries fail.

---

## Indic Intent Model

Scripts:

```bash
python scripts/train_indic_intent_model.py
python scripts/evaluate_indic_intent_model.py
```

Output:

- `models/indic-intent-classifier/model.joblib`
- `models/indic-intent-classifier/metadata.json`
- `reports/model-evaluation/indic_intent_metrics.json`

Latest Generated Metrics (Stratified 34% Test Split):

- **Accuracy:** 33.33% (0.3333)
- **Macro F1:** 29.55% (0.2955)
- **Weighted F1:** 29.66% (0.2966)
- **Classes:** 8 distinct intents (12 queries per intent, total 96 manual sample queries).

Assessment:

The classifier executes the TF-IDF n-gram + Logistic Regression pipeline successfully. However, performance remains weak due to the small size of the demo corpus (only 12 samples per intent spread across English, Hindi, and Odia). For production-ready classification, the dataset needs to be expanded with larger, consented, real-world user interaction corpora.
