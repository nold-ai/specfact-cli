#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

CLI_VERSION="${CLI_VERSION:-0.45.1}"
REPO_SLUG="${REPO_SLUG:-nold-ai/specfact-demo-repo}"
WORK_DIR="${WORK_DIR:-/tmp/specfact-demo-repo}"
CAPTURE_HOME="${CAPTURE_HOME:-/tmp/specfact-readme-capture-home}"
OUTPUT_DIR="${OUTPUT_DIR:-$REPO_ROOT/evidence/readme-sample-output}"
RAW_OUTPUT_PATH="${RAW_OUTPUT_PATH:-$OUTPUT_DIR/review-output.txt}"
SUMMARY_PATH="${SUMMARY_PATH:-$OUTPUT_DIR/README.md}"
INIT_OUTPUT_PATH="${INIT_OUTPUT_PATH:-$OUTPUT_DIR/init-output.txt}"

mkdir -p "$OUTPUT_DIR"
rm -rf "$CAPTURE_HOME"
mkdir -p "$CAPTURE_HOME"

if [[ ! -d "$WORK_DIR/.git" ]]; then
  rm -rf "$WORK_DIR"
  gh repo clone "$REPO_SLUG" "$WORK_DIR"
fi

export HOME="$CAPTURE_HOME"

uvx --from "specfact-cli==$CLI_VERSION" specfact init --profile solo-developer \
  >"$INIT_OUTPUT_PATH" 2>&1

pushd "$WORK_DIR" >/dev/null
uvx \
  --from "specfact-cli==$CLI_VERSION" \
  --with ruff \
  --with radon \
  --with semgrep \
  --with basedpyright \
  --with pylint \
  --with crosshair-tool \
  specfact code review run --path . --scope full \
  >"$RAW_OUTPUT_PATH" 2>&1 || true
popd >/dev/null

cat >"$SUMMARY_PATH" <<EOF
# README sample output capture

- CLI version: \`$CLI_VERSION\`
- Repo: \`$REPO_SLUG\`
- Repo path: \`$WORK_DIR\`
- Capture home: \`$CAPTURE_HOME\`
- Command:

\`\`\`bash
uvx --from "specfact-cli==$CLI_VERSION" specfact init --profile solo-developer
uvx --from "specfact-cli==$CLI_VERSION" --with ruff --with radon --with semgrep --with basedpyright --with pylint --with crosshair-tool specfact code review run --path . --scope full
\`\`\`

- Raw output: \`$RAW_OUTPUT_PATH\`
- Init output: \`$INIT_OUTPUT_PATH\`
EOF
