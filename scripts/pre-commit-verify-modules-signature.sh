#!/usr/bin/env bash
# Legacy entry point for module verify (pre-commit / downstream mirrors).
# Canonical script: pre-commit-verify-modules.sh (branch-aware marketplace-06 policy).
set -euo pipefail
_script_dir=$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)
exec bash "${_script_dir}/pre-commit-verify-modules.sh" "$@"
