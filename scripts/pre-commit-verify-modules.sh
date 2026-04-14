#!/usr/bin/env bash
# Pre-commit / manual entry: branch-aware module verify (marketplace-06 policy).
# Skips when nothing under modules/ or src/specfact_cli/modules/ is staged.
set -euo pipefail

repo_root=$(git rev-parse --show-toplevel 2>/dev/null || true)
if [[ -z "${repo_root}" ]]; then
  echo "❌ Cannot resolve git repository root for module signature verification" >&2
  exit 1
fi
cd "${repo_root}"

staged_files=$(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null || true)
if ! echo "${staged_files}" | grep -qE '^(src/specfact_cli/modules|modules)/'; then
  echo "ℹ️  No staged changes under modules/ or src/specfact_cli/modules/ — skipping module signature verification"
  exit 0
fi

flag_script="${repo_root}/scripts/git-branch-module-signature-flag.sh"
if [[ ! -f "${flag_script}" ]]; then
  echo "❌ Missing ${flag_script}" >&2
  exit 1
fi
sig_policy=$(bash "${flag_script}")
sig_policy="${sig_policy//$'\r'/}"
sig_policy="${sig_policy//$'\n'/}"
case "${sig_policy}" in
  require)
    echo "🔐 Verifying bundled module manifests (--require-signature, --enforce-version-bump, --payload-from-filesystem)" >&2
    exec hatch run ./scripts/verify-modules-signature.py --require-signature --enforce-version-bump --payload-from-filesystem
    ;;
  omit)
    echo "🔐 Verifying bundled module manifests (checksum-only; --enforce-version-bump, --payload-from-filesystem)" >&2
    exec hatch run ./scripts/verify-modules-signature.py --enforce-version-bump --payload-from-filesystem
    ;;
  *)
    echo "❌ Invalid module signature policy from ${flag_script}: '${sig_policy}' (expected require or omit)" >&2
    exit 1
    ;;
esac
