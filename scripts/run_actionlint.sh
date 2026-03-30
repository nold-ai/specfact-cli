#!/usr/bin/env bash
# Actionlint runner.
# - Prefer a globally installed actionlint binary.
# - Otherwise, run the official Docker image when Docker is available and the daemon is reachable.
# - Otherwise, fail with explicit install guidance. Do not download binaries into the repository tree.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
ACTIONLINT_TAG="${ACTIONLINT_TAG:-latest}"
DOCKER_IMAGE="rhysd/actionlint:${ACTIONLINT_TAG}"

run_installed_binary() {
  if ! command -v actionlint >/dev/null 2>&1; then
    return 1
  fi

  actionlint -no-color
}

run_with_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    return 1
  fi

  if ! docker info >/dev/null 2>&1; then
    echo "Docker daemon unavailable for actionlint; falling back to local binary." >&2
    return 1
  fi

  docker run --rm \
      -v "$REPO_ROOT":/repo \
      -w /repo \
      "$DOCKER_IMAGE" -no-color
}

if run_installed_binary; then
  exit 0
fi

if run_with_docker; then
  exit 0
fi

echo "actionlint is required for workflow linting." >&2
echo "Install it globally or use a Docker-enabled environment." >&2
echo "Official install options: https://github.com/rhysd/actionlint" >&2
echo "Example global install:" >&2
echo "  go install github.com/rhysd/actionlint/cmd/actionlint@latest" >&2
exit 2
