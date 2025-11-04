#!/usr/bin/env bash
# Pre-commit checks: YAML lint, GitHub workflow lint, and contract-first smart tests.
# - Always runs YAML/workflow lint when relevant files are staged.
# - Skips tests for safe-only changes (version/docs/test infra), but still enforces YAML/workflow lint.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info()  { echo -e "${BLUE}$*${NC}"; }
success(){ echo -e "${GREEN}$*${NC}"; }
warn()  { echo -e "${YELLOW}$*${NC}"; }
error() { echo -e "${RED}$*${NC}"; }

staged_files() {
  git diff --cached --name-only
}

has_staged_yaml() {
  staged_files | grep -E '\\.ya?ml$' >/dev/null 2>&1
}

has_staged_workflows() {
  staged_files | grep -E '^\.github/workflows/.*\\.ya?ml$' >/dev/null 2>&1
}

run_yaml_lint_if_needed() {
  if has_staged_yaml; then
    info "🔎 YAML changes detected — running yamllint (relaxed)"
    if hatch run yaml-lint; then
      success "✅ YAML lint passed"
    else
      error "❌ YAML lint failed"
      exit 1
    fi
  else
    info "ℹ️  No staged YAML changes — skipping yamllint"
  fi
}

run_actionlint_if_needed() {
  if has_staged_workflows; then
    info "🔎 GitHub workflow changes detected — running actionlint"
    if hatch run lint-workflows; then
      success "✅ Workflow lint passed"
    else
      error "❌ Workflow lint failed"
      exit 1
    fi
  else
    info "ℹ️  No staged workflow YAML changes — skipping actionlint"
  fi
}

check_safe_change() {
  local files
  files=$(staged_files)
  local version_files=("pyproject.toml" "setup.py" "src/__init__.py")
  local changelog_files=("CHANGELOG.md")
  local test_infrastructure_files=(
    "tools/smart_test_coverage.py"
    "scripts/pre-commit-smart-checks.sh"
    "tools/functional_coverage_analyzer.py"
  )
  local doc_patterns=("*.md" "*.rst" "*.txt" "*.json" "*.yaml" "*.yml")
  local doc_dirs=("docs/" "papers/" "presentations/" "images/")

  local version_changes=0
  local test_infra_changes=0
  local doc_changes=0
  local other_changes=0

  for file in $files; do
    local is_safe=false

    if [[ " ${version_files[@]} " =~ " ${file} " ]]; then
      version_changes=$((version_changes + 1))
      is_safe=true
    elif [[ " ${changelog_files[@]} " =~ " ${file} " ]]; then
      doc_changes=$((doc_changes + 1))
      is_safe=true
    elif [[ " ${test_infrastructure_files[@]} " =~ " ${file} " ]]; then
      test_infra_changes=$((test_infra_changes + 1))
      is_safe=true
    elif [[ "$file" == *.md || "$file" == *.rst || "$file" == *.txt || "$file" == *.json || "$file" == *.yaml || "$file" == *.yml ]]; then
      doc_changes=$((doc_changes + 1))
      is_safe=true
    elif [[ "$file" == docs/* || "$file" == papers/* || "$file" == presentations/* || "$file" == images/* ]]; then
      doc_changes=$((doc_changes + 1))
      is_safe=true
    fi

    if [ "$is_safe" = false ]; then
      other_changes=$((other_changes + 1))
    fi
  done

  if [ $other_changes -eq 0 ] && [ $((version_changes + test_infra_changes + doc_changes)) -gt 0 ]; then
    return 0
  fi
  return 1
}

warn "🔍 Running pre-commit checks (YAML/workflows + smart tests)"

# Always run lint checks when relevant files changed
run_yaml_lint_if_needed
run_actionlint_if_needed

# If only safe changes, skip tests after lint passes
if check_safe_change; then
  success "✅ Safe change detected - skipping test run"
  info "💡 Only version numbers, docs/test infra, or YAML/workflows changed"
  exit 0
fi

# Contract-first test flow
if [ ! -f "tools/contract_first_smart_test.py" ]; then
  error "❌ Contract-first test script not found. Please run: hatch run contract-test-full"
  exit 1
fi

if hatch run contract-test-status > /dev/null 2>&1; then
  success "✅ No changes detected - using cached contract test data"
  exit 0
else
  warn "🔄 Changes detected - running contract-first tests for fast feedback..."
  if hatch run contract-test; then
    success "✅ Contract-first tests passed - ready to commit"
    warn "💡 GitHub Actions will run full contract test suite"
    exit 0
  else
    error "❌ Contract-first tests failed"
    warn "💡 Run 'hatch run contract-test-status' for details"
    warn "💡 Or run 'hatch run contract-test-full' for full test suite"
    warn "💡 Legacy: 'hatch run smart-test-force' for smart test suite"
    exit 1
  fi
fi
