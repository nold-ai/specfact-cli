#!/usr/bin/env bash
set -euo pipefail

# yaml-tools.sh: Format and lint YAML and GitHub workflows consistently.
#
# Subcommands:
#   fmt              Format all YAML files (including workflows) with Prettier
#   lint             Lint non-workflow YAML files with yamllint and repo .yamllint
#   workflows-fmt    Format only GitHub workflows with Prettier
#   workflows-lint   Lint GitHub workflows with actionlint (local, bin, or docker fallback)
#   fix-all          Run fmt (covers workflows too)
#   check-all        Run lint + workflows-lint
#
# Usage examples:
#   bash scripts/yaml-tools.sh fmt
#   bash scripts/yaml-tools.sh lint
#   bash scripts/yaml-tools.sh workflows-lint
#   bash scripts/yaml-tools.sh fix-all && bash scripts/yaml-tools.sh check-all

PRETTIER_VERSION="3.3.3"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

run_prettier_all() {
  npx --yes "prettier@${PRETTIER_VERSION}" --log-level warn --cache --write "**/*.{yml,yaml}"
}

run_prettier_workflows() {
  npx --yes "prettier@${PRETTIER_VERSION}" --log-level warn --cache --write ".github/workflows/**/*.{yml,yaml}"
}

run_yamllint() {
  # Lint only non-workflow YAML files, using root .yamllint
  local files
  files=$(git ls-files "*.yml" "*.yaml" | grep -v "^\.github/workflows/" || true)
  if [[ -n "${files}" ]]; then
    # Do not fail on warnings: print all findings, fail only when "error" severity is present
    set +e
    local out
    out=$(yamllint -f standard -c "${REPO_ROOT}/.yamllint" ${files})
    local rc=$?
    set -e
    printf "%s\n" "$out"
    if echo "$out" | grep -q ": error "; then
      return 1
    fi
  fi
}

run_actionlint() {
  if command -v actionlint >/dev/null 2>&1; then
    actionlint -color=never
  elif [[ -x "${REPO_ROOT}/bin/actionlint" ]]; then
    "${REPO_ROOT}/bin/actionlint" -color=never
  elif command -v docker >/dev/null 2>&1; then
    docker run --rm -v "${REPO_ROOT}":/repo -w /repo rhysd/actionlint:latest -no-color
  else
    echo "actionlint not available. Install with:" >&2
    echo "  curl -sSL https://raw.githubusercontent.com/rhysd/actionlint/main/scripts/download-actionlint.bash | bash -s -- -b ./bin" >&2
    exit 2
  fi
}

usage() {
  cat <<EOF
Usage: $0 <subcommand>

Subcommands:
  fmt              Format all YAML files (including workflows) with Prettier
  lint             Lint non-workflow YAML files with yamllint using .yamllint
  workflows-fmt    Format workflows only with Prettier
  workflows-lint   Lint workflows with actionlint
  fix-all          Run fmt (covers workflows) for a repo-wide fix
  check-all        Run lint + workflows-lint (CI-style checks)
EOF
}

main() {
  local cmd=${1:-}
  shift || true
  case "${cmd}" in
    fmt)
      run_prettier_all "$@"
      ;;
    lint)
      run_yamllint "$@"
      ;;
    workflows-fmt)
      run_prettier_workflows "$@"
      ;;
    workflows-lint)
      run_actionlint "$@"
      ;;
    fix-all)
      run_prettier_all "$@"
      ;;
    check-all)
      run_yamllint "$@"
      run_actionlint "$@"
      ;;
    -h|--help|help|"")
      usage
      ;;
    *)
      echo "Unknown subcommand: ${cmd}" >&2
      usage
      exit 1
      ;;
  esac
}

main "$@"
