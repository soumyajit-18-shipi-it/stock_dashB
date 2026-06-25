# Dataset Card: Indic Finance Query Sample

## Dataset Name

Indic Finance Query Sample for Stock Intelligence Dashboard.

## Purpose

The dataset supports lightweight intent classification and language-aware prompt routing for stock analysis, watchlist help, risk explanations, report generation, and financial term explanations.

## Source

Rows were manually authored for this repository as a small sample dataset. No private user data, scraped conversations, or Corpus App exports are included.

## License

Project sample data is released under the repository license unless a future row states a different open license in the `license` column.

## Consent

All current rows have `consent_status=project_authored`. Future user-contributed rows must include documented consent and must not contain account numbers, portfolio holdings, phone numbers, email addresses, or other personal identifiers.

## Schema

See `data/indic/schema.json`.

## Languages and Scripts

- English, Latin script
- Hindi, Devanagari script
- Odia, Odia script

## Intended Use

- Train and evaluate a baseline Indic finance intent classifier.
- Improve multilingual AI chat routing and report prompts.
- Test Hindi/Odia financial terminology handling.

## Out-of-Scope Use

- Financial advice.
- Credit scoring.
- Trading automation.
- User profiling.
- Claims about broad Indic language coverage without collecting a larger representative dataset.

## Bias and Coverage Limitations

This is a small sample corpus. It over-represents common stock dashboard tasks and under-represents dialectal variation, code-mixed queries, speech input, low-literacy phrasing, and regional market terminology beyond a few examples.

## Privacy

The current dataset contains no personal data. If real user feedback is added, it must follow `docs/data-consent.md`, `docs/data-anonymization.md`, and `docs/data-retention.md`.
