# Contributing to Stock Intelligence Dashboard

First off, thank you for considering contributing to the Stock Intelligence Dashboard! It's people like you that make this a great tool for everyone.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## How Can I Contribute?

### Reporting Bugs

* **Check the issue tracker** to see if the bug has already been reported.
* If it hasn't, **open a new issue**. Include a clear title, a description of the bug, steps to reproduce it, and what you expected to happen instead.

### Suggesting Enhancements

* **Open an issue** with the tag "enhancement".
* Describe the feature you'd like to see and why it would be useful.

### Pull Requests

1.  **Fork the repository**.
2.  **Create a new branch** from `main` (e.g., `feature/awesome-feature` or `fix/critical-bug`).
3.  **Make your changes**.
4.  **Ensure your code follows our standards** (see below).
5.  **Run tests** and make sure they pass.
6.  **Submit a Pull Request**.

## Coding Standards

### General

* We use [EditorConfig](.editorconfig) to maintain consistent coding styles.
* Write clean, readable, and well-documented code.
* Follow the [Don't Repeat Yourself (DRY)](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself) principle.

### Python (Backend)

* We follow **PEP 8**.
* Use **Ruff** for linting and formatting.
* Use **Mypy** for static type checking. Always provide type hints.
* Run `ruff check .` and `mypy .` before submitting.

### TypeScript (Frontend)

* Use **ESLint** and **Prettier** for linting and formatting.
* Use functional components and hooks.
* Ensure all new components are properly typed.

## Branch Naming Conventions

*   `feature/...` for new features.
*   `fix/...` for bug fixes.
*   `docs/...` for documentation changes.
*   `refactor/...` for code refactoring.
*   `test/...` for adding or improving tests.

## Commit Message Conventions

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

*   `feat: ...` for a new feature.
*   `fix: ...` for a bug fix.
*   `docs: ...` for documentation changes.
*   `style: ...` for changes that do not affect the meaning of the code (white-space, formatting, etc).
*   `refactor: ...` for code changes that neither fix a bug nor add a feature.
*   `perf: ...` for code changes that improve performance.
*   `test: ...` for adding missing tests or correcting existing tests.
*   `chore: ...` for changes to the build process or auxiliary tools and libraries.

## Testing Requirements

*   **Unit Tests:** Every new feature or fix should be accompanied by unit tests.
*   **Coverage:** We aim for 90%+ code coverage. Use `pytest --cov` to check coverage.
*   **Regression Tests:** Ensure that your changes do not break existing functionality.

## Development Setup

See the [User Manual](USER_MANUAL.md) for instructions on setting up your development environment.
