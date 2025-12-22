#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_DIR="${SCRIPT_DIR}"

TARGET_DIR="${1:-}"
REPO_PATH="${2:-}"
BUNDLE_NAME="${3:-}"

if [[ -z "${TARGET_DIR}" ]]; then
  echo "Usage: ${0} <target_dir> [repo_path] [bundle_name]"
  exit 1
fi

mkdir -p "${TARGET_DIR}"
cp -R "${TEMPLATE_DIR}/." "${TARGET_DIR}/"

if [[ -n "${REPO_PATH}" && -n "${BUNDLE_NAME}" ]]; then
  cat > "${TARGET_DIR}/.env" <<EOF
REPO_PATH=${REPO_PATH}
BUNDLE_NAME=${BUNDLE_NAME}
REPO_PYTHONPATH=${REPO_PATH}/src:${REPO_PATH}
RUN_BASEDPYRIGHT=0
BINDINGS_PATH=bindings.yaml
FEATURES_DIR=${REPO_PATH}/.specfact/projects/${BUNDLE_NAME}/features
EOF
  echo "[sidecar-init] wrote ${TARGET_DIR}/.env"
fi

echo "[sidecar-init] sidecar templates copied to ${TARGET_DIR}"
