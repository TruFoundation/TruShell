#!/usr/bin/env bash
set -euo pipefail

if ! command -v trushell >/dev/null 2>&1; then
  echo "trushell is not installed or not in PATH"
  exit 2
fi

if trushell --version >/dev/null 2>&1; then
  echo "Version check succeeded"
else
  echo "trushell --version failed"
  exit 1
fi

if trushell -c 'echo packaging-smoke' >/dev/null 2>&1; then
  echo "Smoke command succeeded"
else
  echo "trushell -c failed"
  exit 1
fi
