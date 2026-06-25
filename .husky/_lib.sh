#!/usr/bin/env sh
# Cross-platform POSIX helpers for Husky hooks.
# Husky 9 shims always invoke hooks with `sh`, so this stays POSIX-portable
# on Windows (Git Bash), macOS, and Linux.
#
# Sourced by pre-commit, pre-push, and commit-msg.

# Locate repo root (parent of .husky/).
HUSKY_REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$(cd "$(dirname "$0")/.." && pwd)")"
export HUSKY_REPO_ROOT

# Detect npx (Node) and python (>=3.8).
HUSKY_NPX="npx --no-install"
HUSKY_PYTHON="$(command -v python 2>/dev/null || command -v python3 2>/dev/null || echo python)"
HUSKY_PRE_COMMIT="pre-commit"

# Color helpers (no-op when not a TTY).
if [ -t 1 ]; then
  HUSKY_RED='\033[0;31m'
  HUSKY_GREEN='\033[0;32m'
  HUSKY_YELLOW='\033[0;33m'
  HUSKY_BLUE='\033[0;34m'
  HUSKY_NC='\033[0m'
else
  HUSKY_RED=''; HUSKY_GREEN=''; HUSKY_YELLOW=''; HUSKY_BLUE=''; HUSKY_NC=''
fi

husky_log()  { printf "${HUSKY_BLUE}[husky]${HUSKY_NC} %s\n" "$*"; }
husky_ok()   { printf "${HUSKY_GREEN}[husky]${HUSKY_NC} %s\n" "$*"; }
husky_warn() { printf "${HUSKY_YELLOW}[husky]${HUSKY_NC} %s\n" "$*"; }
husky_err()  { printf "${HUSKY_RED}[husky]${HUSKY_NC} %s\n" "$*" >&2; }

# Print command and run it; abort on failure.
husky_run() {
  husky_log "▶ $*"
  "$@" || { husky_err "✗ command failed: $*"; exit 1; }
}

# Skip the entire hook if $HUSKY=0 (escape hatch for CI / quick WIP commits).
if [ "${HUSKY:-1}" = "0" ]; then
  husky_warn "HUSKY=0, skipping hook"
  exit 0
fi
