#!/usr/bin/env bash
# Actionlint runner: Docker-first with binary fallback.
# - If Docker is available, run the actionlint container from Docker Hub (latest by default; override with ACTIONLINT_TAG).
# - Otherwise, download a pinned fallback actionlint binary into tools/bin and execute it.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
BIN_DIR="$REPO_ROOT/tools/bin"
ACTIONLINT_TAG="${ACTIONLINT_TAG:-latest}"
ACTIONLINT_FALLBACK_VERSION="1.7.1"
DOCKER_IMAGE="rhysd/actionlint:${ACTIONLINT_TAG}"

run_with_docker() {
  if command -v docker >/dev/null 2>&1; then
  docker run --rm \
      -v "$REPO_ROOT":/repo \
      -w /repo \
      "$DOCKER_IMAGE" -no-color
    return 0
  fi
  return 1
}

ensure_binary() {
  mkdir -p "$BIN_DIR"
  if [[ -x "$BIN_DIR/actionlint" ]]; then
    return 0
  fi

  echo "Downloading actionlint v${ACTIONLINT_FALLBACK_VERSION} binary..." >&2
  ARCHIVE="actionlint_${ACTIONLINT_FALLBACK_VERSION}_linux_amd64.tar.gz"
  URL="https://github.com/rhysd/actionlint/releases/download/v${ACTIONLINT_FALLBACK_VERSION}/${ARCHIVE}"

  TMPDIR="$(mktemp -d)"
  trap 'rm -rf "$TMPDIR"' EXIT

  curl -sSL "$URL" -o "$TMPDIR/$ARCHIVE"
  tar -xzf "$TMPDIR/$ARCHIVE" -C "$TMPDIR"
  install -m 0755 "$TMPDIR/actionlint" "$BIN_DIR/actionlint"
}

run_binary() {
  "$BIN_DIR/actionlint" -no-color
}

# Prefer Docker; if not available, use binary fallback.
if run_with_docker; then
  exit 0
fi

ensure_binary
run_binary
