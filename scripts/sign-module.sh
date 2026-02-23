#!/usr/bin/env bash
# Sign module manifest for integrity metadata (checksum and optional signature).
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  scripts/sign-module.sh [--key-file PATH] [--passphrase TEXT|--passphrase-stdin] [--allow-unsigned] [--allow-same-version] <path-to-module-package.yaml>

Options:
  --key-file PATH     PEM private key used for detached signatures (recommended)
  --passphrase TEXT   Passphrase for encrypted private key (discouraged in shell history)
  --passphrase-stdin  Read passphrase from stdin (for secure piping/CI use)
  --allow-unsigned    Allow checksum-only signing without key (local testing only)
  --allow-same-version  Bypass version-bump enforcement before signing (not recommended)
  -h, --help          Show this help message
EOF
}

KEY_FILE=""
PASSPHRASE=""
PASSPHRASE_STDIN=0
ALLOW_UNSIGNED=0
ALLOW_SAME_VERSION=0
MANIFEST=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --key-file)
      shift
      if [[ $# -eq 0 ]]; then
        echo "Error: --key-file requires a path argument." >&2
        usage >&2
        exit 1
      fi
      KEY_FILE="$1"
      ;;
    --allow-unsigned)
      ALLOW_UNSIGNED=1
      ;;
    --allow-same-version)
      ALLOW_SAME_VERSION=1
      ;;
    --passphrase)
      shift
      if [[ $# -eq 0 ]]; then
        echo "Error: --passphrase requires a value." >&2
        usage >&2
        exit 1
      fi
      PASSPHRASE="$1"
      ;;
    --passphrase-stdin)
      PASSPHRASE_STDIN=1
      ;;
    --*)
      echo "Error: unknown option '$1'." >&2
      usage >&2
      exit 1
      ;;
    *)
      if [[ -n "$MANIFEST" ]]; then
        echo "Error: only one manifest path is supported by this wrapper." >&2
        usage >&2
        exit 1
      fi
      MANIFEST="$1"
      ;;
  esac
  shift
done

if [[ -z "$MANIFEST" || ! -f "$MANIFEST" ]]; then
  echo "Error: manifest path is required and must exist." >&2
  usage >&2
  exit 1
fi

ARGS=()
if [[ -n "$KEY_FILE" ]]; then
  ARGS+=(--key-file "$KEY_FILE")
fi
if [[ -n "$PASSPHRASE" ]]; then
  ARGS+=(--passphrase "$PASSPHRASE")
fi
if [[ "$PASSPHRASE_STDIN" -eq 1 ]]; then
  ARGS+=(--passphrase-stdin)
fi
if [[ "$ALLOW_UNSIGNED" -eq 1 ]]; then
  ARGS+=(--allow-unsigned)
fi
if [[ "$ALLOW_SAME_VERSION" -eq 1 ]]; then
  ARGS+=(--allow-same-version)
fi
python3 scripts/sign-modules.py "${ARGS[@]}" "$MANIFEST"

# Emit checksum line for legacy pipeline compatibility.
python3 - "$MANIFEST" <<'PY'
from pathlib import Path
import yaml
import sys

manifest = Path(sys.argv[1])
data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
integrity = data.get("integrity") if isinstance(data, dict) else None
checksum = integrity.get("checksum") if isinstance(integrity, dict) else ""
print(checksum)
print(f"checksum: {checksum}", file=sys.stderr)
PY
