# Data Anonymization

## Rules for Query/Feedback Data

Before adding real user data to datasets:

- Remove names, email addresses, phone numbers, account IDs, and brokerage IDs.
- Remove exact holdings or portfolio values unless explicitly needed and consented.
- Replace rare personal details with generic placeholders.
- Keep only task-relevant fields: language, intent, normalized query, and optional ticker.

## Validation

Dataset maintainers should review rows manually in addition to running `scripts/validate_indic_dataset.py`.
