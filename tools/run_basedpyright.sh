#!/usr/bin/env bash
# Execute the committed BasedPyright npm package without network resolution.
set -euo pipefail

script_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(CDPATH= cd -- "$script_dir/.." && pwd -P)"
runner="$repo_root/tools/basedpyright/node_modules/basedpyright/index.js"
if [ ! -f "$runner" ]; then
  echo "BasedPyright is not installed. Run: npm ci --ignore-scripts --prefix tools/basedpyright" >&2
  exit 1
fi

exec node "$runner" "$@"
