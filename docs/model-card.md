# Model Card

## Project

Stock Intelligence Dashboard.

## Intended Use

The models support exploratory stock analysis, chart context, watchlist workflows, and education. Outputs are not financial advice and must not be used as the sole basis for trading or investment decisions.

## Users

Individual investors, students, researchers, traders, and analysts who need a compact dashboard for public market data exploration.

## Models

| Model | Type | Source / License | Purpose | Open Source |
| --- | --- | --- | --- | --- |
| Linear Regression | scikit-learn regression pipeline with StandardScaler | scikit-learn, BSD-3-Clause | Next-day close price baseline | Yes |
| Random Forest Regressor | scikit-learn ensemble regression | scikit-learn, BSD-3-Clause | Non-linear next-day close price prediction | Yes |
| Ensemble Arbitration | Project code | Repository license | Blend or select model based on confidence | Yes |
| Indic Intent Classifier | TF-IDF char n-grams + Logistic Regression | scikit-learn, BSD-3-Clause; project sample dataset | Classify multilingual finance query intent | Yes |
| LLM Providers | Groq, OpenAI, Anthropic, Gemini, OpenRouter, Ollama | Provider-specific terms | AI chat and report generation | Mixed: Ollama can run local open models; hosted providers are external/closed APIs |

## Inputs

Stock prediction inputs:

- Historical OHLCV data from Yahoo Finance/yfinance.
- Features: close, volume, MA7, MA21, returns, lag1-lag5, volume change.

Indic intent inputs:

- Query text and language prefix from `data/indic/sample_indic_finance_queries.csv`.

LLM inputs:

- User prompt.
- Stock context injected by `frontend/src/services/aiProviderService.ts`: ticker, company, exchange, sector, industry, current price, prediction, metrics, recent candles.

## Outputs

- Predicted next-day close price.
- Trend direction.
- Confidence score.
- RMSE, MAE, R2 for the training split.
- Indic query intent and confidence when the local classifier artifact exists.
- AI-generated chat/report text from the selected provider.

## Training Data

Stock models train on public market data fetched per ticker/range. The Indic intent classifier trains on the project-authored sample corpus in `data/indic/`.

## Evaluation

See `docs/model-evaluation.md` and `reports/model-evaluation/`. Stock metrics are generated from the existing chronological 80/20 split. Indic intent metrics are generated from a deterministic train/test split of the sample corpus.

## Limitations

- Stock prices are noisy and affected by events not present in OHLCV features.
- Historical fit metrics do not guarantee future performance.
- The Indic dataset is small and not representative of all Indian users.
- LLM outputs can be wrong, stale, or overconfident.
- External provider privacy and retention policies apply when using hosted LLM APIs.

## Bias and Fairness

The app currently covers English, Hindi, and Odia in the sample dataset and five UI locales. Other Indian languages need consented/open-licensed data before claims of coverage can be made.

## Privacy

Local stock models use public market data. AI chat prompts may be sent to external providers unless Ollama/local mode is selected. See `PRIVACY.md` and `docs/ai-transparency.md`.

## Out-of-Scope Use

- Personalized investment advice.
- Automated trading.
- Credit, lending, insurance, or employment decisions.
- Claims of guaranteed returns.
