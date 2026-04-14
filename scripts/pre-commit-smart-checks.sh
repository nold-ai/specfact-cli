#!/usr/bin/env bash
# Back-compat entry: single hook for downstream repos that pin `specfact-smart-checks`.
# Canonical layout is modular hooks in .pre-commit-config.yaml → pre-commit-quality-checks.sh.
#
# Resolves the quality script from the repository root so copies under .git/hooks/pre-commit work.
set -euo pipefail

_script_path=${BASH_SOURCE[0]}
case "${_script_path}" in
  /*) ;;
  *) _script_path=$(pwd)/${_script_path} ;;
esac
_hook_dir=$(CDPATH= cd -- "$(dirname "${_script_path}")" && pwd)

_repo_root=$(git -C "${_hook_dir}" rev-parse --show-toplevel)

exec bash "${_repo_root}/scripts/pre-commit-quality-checks.sh" all "$@"
