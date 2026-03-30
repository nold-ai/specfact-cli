#!/usr/bin/env bash
# Actionlint runner.
# - Prefer a globally installed actionlint binary.
# - Otherwise, run the official Docker image when Docker is available and the daemon is reachable.
# - Otherwise, fail with explicit install guidance. Do not download binaries into the repository tree.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
ACTIONLINT_TAG="${ACTIONLINT_TAG:-v1.7.11}"
DOCKER_IMAGE="rhysd/actionlint:${ACTIONLINT_TAG}"

has_actionlint() {
  command -v actionlint >/dev/null 2>&1
}

has_docker() {
  command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1
}

if has_actionlint; then
  cd "$REPO_ROOT"
  actionlint -no-color
  exit $?
fi

if has_docker; then
  docker run --rm \
      -v "$REPO_ROOT":/repo \
      -w /repo \
      "$DOCKER_IMAGE" -no-color
  exit $?
fi

echo "actionlint is required for workflow linting." >&2
echo "Install it globally or use a Docker-enabled environment." >&2
echo "Official install options: https://github.com/rhysd/actionlint" >&2
echo "Example global install:" >&2
echo "  go install github.com/rhysd/actionlint/cmd/actionlint@${ACTIONLINT_TAG}" >&2
exit 2
