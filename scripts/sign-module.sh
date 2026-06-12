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

# Enforce version bump for changed module payload before any signing/key checks.
if [[ "$ALLOW_SAME_VERSION" -ne 1 ]]; then
  python3 - "$MANIFEST" <<'PY'
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml


def _run(cmd: list[str]) -> str:
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout.strip()


manifest = Path(sys.argv[1]).resolve()
module_dir = manifest.parent

try:
    current_raw = yaml.safe_load(manifest.read_text(encoding="utf-8"))
except Exception as exc:
    print(f"Error: failed reading manifest {manifest}: {exc}", file=sys.stderr)
    raise SystemExit(1) from exc

if not isinstance(current_raw, dict):
    print(f"Error: invalid manifest YAML (expected object): {manifest}", file=sys.stderr)
    raise SystemExit(1)

current_version = str(current_raw.get("version", "")).strip()
if not current_version:
    print(f"Error: manifest missing version: {manifest}", file=sys.stderr)
    raise SystemExit(1)

try:
    manifest_rel = manifest.relative_to(Path.cwd().resolve()).as_posix()
except ValueError:
    # Outside current repo root: skip git-based preflight and let signer handle it.
    raise SystemExit(0)
try:
    previous_text = _run(["git", "show", f"HEAD:{manifest_rel}"])
except Exception:
    raise SystemExit(0)

try:
    previous_raw = yaml.safe_load(previous_text)
except Exception:
    raise SystemExit(0)
if not isinstance(previous_raw, dict):
    raise SystemExit(0)

previous_version = str(previous_raw.get("version", "")).strip()
if not previous_version or previous_version != current_version:
    raise SystemExit(0)

try:
    changed = _run(["git", "diff", "--name-only", "HEAD", "--", module_dir.as_posix()])
    untracked = _run(["git", "ls-files", "--others", "--exclude-standard", "--", module_dir.as_posix()])
except Exception:
    raise SystemExit(0)

if changed or untracked:
    print(
        "Error: Module version must be incremented before signing changed module contents: "
        f"{manifest_rel} (current version {current_version}).",
        file=sys.stderr,
    )
    raise SystemExit(1)
PY
fi

if [[ "${#ARGS[@]}" -gt 0 ]]; then
  python3 scripts/sign-modules.py "${ARGS[@]}" "$MANIFEST"
else
  python3 scripts/sign-modules.py "$MANIFEST"
fi

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
