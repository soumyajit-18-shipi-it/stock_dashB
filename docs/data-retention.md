# Data Retention

## Application Data

- Watchlists and search history: retain until the user deletes them or account deletion is requested.
- Prediction records: retain until deleted by the user/maintainer policy.
- AI provider keys: stored only in browser `localStorage`; users can clear browser storage.

## Dataset Rows

Project-authored rows can remain indefinitely. User-contributed rows should be reviewed at least annually and deleted on request.

## Logs

Backend request logs should not include API keys or full user prompts. Production log retention should be set by deployment policy and documented by operators.
