# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-06-12

### Added

- Initial release of Stock Intelligence Dashboard.
- FastAPI backend with Scikit-Learn integration.
- React frontend with Plotly charts.
- Supabase integration for persistence and auth.
- ML models for stock price prediction (Random Forest, Linear Regression).
- Technical indicator engineering (RSI, MA).
- AI report generation (PDF).
- Ask AI feature for market insights.
- Comprehensive documentation (CONTRIBUTING.md, USER_MANUAL.md, AGENTS.md, SECURITY.md, CODE_OF_CONDUCT.md).
- Compliance and health files (.editorconfig, .dockerignore, LICENSE).
- Production-ready Dockerfile.
- GitLab CI configuration.
- Pre-commit hooks for code quality.
- Automatic changelog generation with git-cliff.
- Spec-Kit initialization.

### Changed

- Refactored backend services for better modularity.
- Optimized frontend state management with Zustand.

### Fixed

- Fixed various linting and typing issues.
- Improved error handling for API rate limits.
