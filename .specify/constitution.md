# Project Constitution: Stock Intelligence Dashboard

This document defines the foundational principles, standards, and requirements for the Stock Intelligence Dashboard project.

## 1. Architecture Principles

*   **Decoupled Design:** Maintain a clear separation between the frontend (React) and backend (FastAPI). Communicate exclusively via RESTful APIs.
*   **Stateless Backend:** The backend should be stateless whenever possible. Use Supabase for persistence.
*   **ML Precision:** ML models should be deterministic and isolated from business logic. Feature engineering should be reusable and tested.
*   **Scalability:** Design for horizontal scaling. Use caching (e.g., Redis) for frequently accessed data.

## 2. Coding Principles

*   **Explicit over Implicit:** Write clear, self-documenting code. Avoid "magic" and hidden side effects.
*   **Strict Typing:** Use strict typing in both Python (Mypy) and TypeScript (TSC). No `any` or `type: ignore` without strong justification.
*   **DRY (Don't Repeat Yourself):** Extract common logic into services, hooks, or utility functions.
*   **KISS (Keep It Simple, Stupid):** Prioritize simplicity and readability over complex abstractions.

## 3. Testing Requirements

*   **90%+ Coverage:** All new code must be accompanied by tests. Maintain a minimum of 90% code coverage.
*   **Empirical Reproduction:** Bug fixes must include a reproduction test case that fails before the fix and passes after.
*   **Automated Validation:** All tests must pass in the CI/CD pipeline.

## 4. Security Requirements

*   **No Exposed Secrets:** Never commit API keys, passwords, or sensitive configuration. Use environment variables.
*   **Input Validation:** Sanitize and validate all user inputs on both frontend and backend.
*   **Dependency Auditing:** Regularly scan dependencies for known vulnerabilities.
*   **Secure Communication:** Use HTTPS for all production traffic.

## 5. Performance Requirements

*   **Lighthouse Score:** Aim for 90+ in all Lighthouse categories (Performance, Accessibility, Best Practices, SEO).
*   **API Latency:** Target <200ms for standard API requests (excluding ML inference).
*   **Optimized Assets:** Minimize bundle sizes and optimize images/charts for fast loading.

## 6. Documentation Standards

*   **Living Documentation:** Keep `README.md`, `USER_MANUAL.md`, and `AGENTS.md` up to date with architectural changes.
*   **Changelog:** Document all notable changes in `CHANGELOG.md` using the Keep-a-Changelog format.
*   **Inline Comments:** Use comments to explain "why", not "what". Code should explain "what".
