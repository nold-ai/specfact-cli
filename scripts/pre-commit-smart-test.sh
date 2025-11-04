#!/usr/bin/env bash
# This script has been renamed. Please use scripts/pre-commit-smart-checks.sh
# For backward compatibility, we forward to the new script.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$SCRIPT_DIR/pre-commit-smart-checks.sh"
