#!/usr/bin/env bash
# Invoke verify-modules-signature.py with flags from scripts/module-verify-policy.sh
# (single source of truth for VERIFY_MODULES_* bundles).
set -euo pipefail
ROOT=$(cd "$(dirname "$0")" && pwd)
# shellcheck disable=SC1090
source "${ROOT}/module-verify-policy.sh"
mode=${1:?usage: run_verify_modules_policy.sh strict|pr|push-orchestrator -- [extra args]}
shift
case "${mode}" in
  strict)
    exec python "${ROOT}/verify-modules-signature.py" "${VERIFY_MODULES_STRICT[@]}" "$@"
    ;;
  pr)
    exec python "${ROOT}/verify-modules-signature.py" "${VERIFY_MODULES_PR[@]}" "$@"
    ;;
  push-orchestrator)
    exec python "${ROOT}/verify-modules-signature.py" "${VERIFY_MODULES_PUSH_ORCHESTRATOR[@]}" "$@"
    ;;
  *)
    echo "run_verify_modules_policy.sh: unknown mode ${mode} (expected strict|pr|push-orchestrator)" >&2
    exit 2
    ;;
esac
