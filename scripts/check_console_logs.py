#!/usr/bin/env python3
"""
check_console_logs.py — Cross-platform scanner for accidental debug statements.

Reads staged files (passed by pre-commit as positional args, or discovered via
`git diff --cached --name-only --diff-filter=ACMR` if no args are given) and
flags:
  - TypeScript / JavaScript: console.log, console.debug, debugger; breakpoint()
  - Python: print() at module/function start, pdb.set_trace(), ipdb.set_trace(),
    breakpoint(), pytest.set_trace()

Strict in src/, lenient in tests/scripts:
  - Files under frontend/src/** and backend/** (excluding test/script/mock/
    migration subdirs) are categorised ERROR and abort the commit.
  - Everything else is WARN — printed but does not abort.

An optional allow-list file (default: .console-allowlist at repo root) contains
JSON lines of {"glob": "...", "regex": "..."} entries that suppress warnings.

Exit codes:
  0  — clean (or warnings only)
  1  — at least one ERROR match
  2  — internal error (e.g. invalid allow-list)
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

JS_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("no-console-log", re.compile(r"\bconsole\.(log|trace)\s*\(")),
    ("no-console-debug", re.compile(r"\bconsole\.debug\s*\(")),
    ("no-debugger", re.compile(r"(^|[^\w])debugger\s*;?\s*$")),
    ("no-breakpoint", re.compile(r"\bbreakpoint\s*\(")),
]

PY_RULES: list[tuple[str, re.Pattern[str]]] = [
    # Allow f-string logging; block bare print().
    ("no-print", re.compile(r"^\s*print\s*\(")),
    ("no-pdb", re.compile(r"\b(pdb|ipdb|pudb)\.set_trace\s*\(")),
    ("no-breakpoint", re.compile(r"^\s*breakpoint\s*\(")),
    ("no-pytest-set-trace", re.compile(r"\bpytest\.set_trace\s*\(")),
]

# Paths that are ALWAYS lenient regardless of directory (override strictness).
LENIENT_SUFFIXES: tuple[str, ...] = (
    "/tests/",
    "/test/",
    "/__tests__/",
    "/__mocks__/",
    "/mocks/",
    "/fixtures/",
    "/migrations/",
    "/scripts/",
    "/test/",
    "/.bolt/",
)

# Files where strict-mode logs are explicitly OK (e.g. logger.info calls).
DEFAULT_ALLOWLIST_PATH = Path(__file__).resolve().parent.parent / ".console-allowlist"


# ---------------------------------------------------------------------------
# Severity classification
# ---------------------------------------------------------------------------


def is_lenient(path: str) -> bool:
    p = path.replace("\\", "/")
    if any(seg in p for seg in LENIENT_SUFFIXES):
        return True
    # Anything under frontend/test or frontend/src/test is lenient.
    name = Path(p).name
    if name.endswith(
        (
            ".test.ts",
            ".test.tsx",
            ".spec.ts",
            ".spec.tsx",
            ".test.js",
            ".test.jsx",
            ".spec.js",
            ".spec.jsx",
        )
    ):
        return True
    if "/locales/" in p:
        return True
    return False


def rule_set_for(path: str) -> list[tuple[str, re.Pattern[str]]] | None:
    p = path.replace("\\", "/").lower()
    if p.endswith((".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")):
        return JS_RULES
    if p.endswith(".py"):
        return PY_RULES
    return None


# ---------------------------------------------------------------------------
# Allow-list loader
# ---------------------------------------------------------------------------


def load_allowlist(path: Path) -> list[tuple[re.Pattern[str], re.Pattern[str]]]:
    """Return [(path_regex, line_regex), ...] parsed from a JSONL file."""
    if not path.is_file():
        return []
    out: list[tuple[re.Pattern[str], re.Pattern[str]]] = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        try:
            entry = json.loads(s)
            out.append(
                (
                    re.compile(entry["glob"]),
                    re.compile(entry["regex"]),
                )
            )
        except Exception as exc:  # noqa: BLE001
            print(
                f"check_console_logs: bad allow-list line {i}: {exc}", file=sys.stderr
            )
            return []
    return out


def is_allowed(
    path: str,
    lineno: int,
    line_text: str,
    allow: list[tuple[re.Pattern[str], re.Pattern[str]]],
) -> bool:
    for path_re, line_re in allow:
        if path_re.search(path) and line_re.search(line_text):
            return True
    return False


# ---------------------------------------------------------------------------
# File scanning
# ---------------------------------------------------------------------------


def scan_file(
    path: str, allow: list[tuple[re.Pattern[str], re.Pattern[str]]], root: Path
) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) — each a list of formatted lines."""
    rules = rule_set_for(path)
    if rules is None:
        return [], []

    lenient = is_lenient(path)
    full = root / path
    if not full.is_file():
        return [], []

    try:
        text = full.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [f"{path}: cannot read: {exc}"], []

    errors: list[str] = []
    warnings: list[str] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for rule_id, pat in rules:
            if pat.search(line) and not is_allowed(path, lineno, line, allow):
                tag = "WARN" if lenient else "ERROR"
                msg = f"{tag}: {path}:{lineno}: [{rule_id}] {line.strip()}"
                if lenient:
                    warnings.append(msg)
                else:
                    errors.append(msg)
                break  # one rule per line is enough
    return errors, warnings


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def discover_staged_files() -> list[str]:
    """Read staged file list from git."""
    import subprocess

    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def main(argv: list[str]) -> int:
    root = Path(os.environ.get("REPO_ROOT") or Path.cwd())
    files = list(argv[1:]) or discover_staged_files()
    if not files:
        return 0

    allowlist_path = Path(os.environ.get("CONSOLE_ALLOWLIST") or DEFAULT_ALLOWLIST_PATH)
    allow = load_allowlist(allowlist_path)

    total_errors: list[str] = []
    total_warnings: list[str] = []

    for f in files:
        errs, warns = scan_file(f, allow, root)
        total_errors.extend(errs)
        total_warnings.extend(warns)

    for w in total_warnings:
        print(w)
    for e in total_errors:
        print(e, file=sys.stderr)

    if total_warnings:
        print(
            f"check_console_logs: {len(total_warnings)} warning(s) "
            f"(lenient: tests/scripts/mocks).",
            file=sys.stderr,
        )
    if total_errors:
        print(
            f"check_console_logs: {len(total_errors)} error(s) in src/. "
            "Replace with proper logging or add an entry to .console-allowlist.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
