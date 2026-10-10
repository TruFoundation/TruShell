#!/usr/bin/env bash
set -euo pipefail

# Checks the trushell on PATH, as installed by a package or a release build.
#
# Each check looks at the output, not just the exit status: a trushell that
# ignores its arguments starts the REPL, reads EOF from /dev/null and exits
# 0, which would otherwise pass both checks without testing anything.
# stdin is /dev/null and each run is time-limited so a REPL can't hang CI.

run() {
  if command -v timeout >/dev/null 2>&1; then
    timeout 10 "$@" </dev/null
  else
    "$@" </dev/null
  fi
}

if ! command -v trushell >/dev/null 2>&1; then
  echo "trushell is not installed or not in PATH"
  exit 2
fi

if out=$(run trushell --version 2>&1) && grep -Eq '[0-9]+\.[0-9]+\.[0-9]+' <<<"$out"; then
  echo "Version check succeeded: $out"
else
  echo "trushell --version did not print a version. Output was:"
  echo "$out"
  exit 1
fi

if out=$(run trushell -c 'echo packaging-smoke' 2>/dev/null) && grep -qx 'packaging-smoke' <<<"$out"; then
  echo "Smoke command succeeded"
else
  echo "trushell -c 'echo packaging-smoke' did not print packaging-smoke. Output was:"
  echo "$out"
  exit 1
fi
