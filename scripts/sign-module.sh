#!/usr/bin/env bash
# Sign module manifest for integrity (arch-06). Outputs checksum in algo:hex format for manifest integrity field.
set -euo pipefail
MANIFEST="${1:-}"
if [[ -z "$MANIFEST" || ! -f "$MANIFEST" ]]; then
  echo "Usage: $0 <path-to-module-package.yaml>" >&2
  exit 1
fi
# Produce sha256 checksum for manifest content (integrity.checksum format)
if command -v sha256sum &>/dev/null; then
  SUM=$(sha256sum -b < "$MANIFEST" | awk '{print $1}')
elif command -v shasum &>/dev/null; then
  SUM=$(shasum -a 256 -b < "$MANIFEST" | awk '{print $1}')
else
  echo "No sha256sum/shasum found" >&2
  exit 1
fi
echo "sha256:$SUM"
echo "checksum: sha256:$SUM" >&2
