#!/usr/bin/env bash
# Emit verify-modules-signature.py signature policy flag for the current git branch.
# Prints --require-signature on main; --allow-unsigned elsewhere (including detached HEAD).
set -euo pipefail

branch=""
branch=$(git branch --show-current 2>/dev/null || true)
if [[ -z "${branch}" || "${branch}" == "HEAD" ]]; then
  branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)
fi
if [[ "${branch}" == "main" ]]; then
  printf '%s\n' "--require-signature"
else
  printf '%s\n' "--allow-unsigned"
fi
