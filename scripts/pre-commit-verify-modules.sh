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

# Include deletions (D): removed paths under modules/ must still trigger verification.
staged_files=$(git diff --cached --name-only --diff-filter=ACMRD) || {
  echo "❌ Error discovering staged files (git diff --cached failed)" >&2
  exit 1
}
if ! echo "${staged_files}" | grep -qE '^(src/specfact_cli/modules|modules)/'; then
  echo "ℹ️  No staged changes under modules/ or src/specfact_cli/modules/ — skipping module signature verification"
  exit 0
fi

mapfile -t staged_manifests < <(
  printf '%s\n' "${staged_files}" \
    | python3 -c '
from pathlib import Path
import sys

seen = set()
for raw in sys.stdin:
    path = Path(raw.strip())
    if not path.parts:
        continue
    parts = path.parts
    manifest = None
    if len(parts) >= 4 and parts[:3] == ("src", "specfact_cli", "modules"):
        manifest = Path(*parts[:4]) / "module-package.yaml"
    elif len(parts) >= 2 and parts[0] == "modules":
        manifest = Path(*parts[:2]) / "module-package.yaml"
    if manifest is not None and manifest not in seen:
        print(manifest.as_posix())
        seen.add(manifest)
'
)

flag_script="${repo_root}/scripts/git-branch-module-signature-flag.sh"
policy_script="${repo_root}/scripts/module-verify-policy.sh"
if [[ ! -f "${flag_script}" ]]; then
  echo "❌ Missing ${flag_script}" >&2
  exit 1
fi
if [[ ! -f "${policy_script}" ]]; then
  echo "❌ Missing ${policy_script}" >&2
  exit 1
fi
# shellcheck disable=SC1090
source "${policy_script}"
sig_policy=$(bash "${flag_script}")
sig_policy="${sig_policy//$'\r'/}"
sig_policy="${sig_policy//$'\n'/}"
case "${sig_policy}" in
  require)
    echo "🔐 Verifying bundled module manifests (strict: require-signature + checksum + version bump)" >&2
    exec hatch run ./scripts/verify-modules-signature.py "${VERIFY_MODULES_STRICT[@]}"
    ;;
  omit)
    if [[ "${#staged_manifests[@]}" -gt 0 ]]; then
      echo "🔐 Auto-bumping changed bundled module versions (patch) before relaxed verification" >&2
      hatch run ./scripts/sign-modules.py --version-only --bump-version patch --base-ref HEAD "${staged_manifests[@]}"
      git add -- "${staged_manifests[@]}"
    fi
    echo "🔐 Verifying module version bumps only (checksum/signature deferred to CI on non-main)" >&2
    exec hatch run ./scripts/verify-modules-signature.py "${VERIFY_MODULES_PR[@]}"
    ;;
  *)
    echo "❌ Invalid module signature policy from ${flag_script}: '${sig_policy}' (expected require or omit)" >&2
    exit 1
    ;;
esac
