#!/usr/bin/env bash
# Back-compat entry: single hook for downstream repos that pin `specfact-smart-checks`.
# Canonical layout is modular hooks in .pre-commit-config.yaml → pre-commit-quality-checks.sh.
set -euo pipefail
exec "$(dirname "$0")/pre-commit-quality-checks.sh" all "$@"
