#!/usr/bin/env bash
# Emit module signature policy for the current git branch (consumed by pre-commit-verify-modules.sh).
# Prints a single token: "require" on main → VERIFY_MODULES_STRICT from module-verify-policy.sh;
# "omit" elsewhere → VERIFY_MODULES_PR (version bump only; checksum/signature deferred to CI).
set -euo pipefail

branch=""
branch=$(git branch --show-current 2>/dev/null || true)
if [[ -z "${branch}" || "${branch}" == "HEAD" ]]; then
  branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)
fi
if [[ "${branch}" == "main" ]]; then
  printf '%s\n' "require"
else
  printf '%s\n' "omit"
fi
