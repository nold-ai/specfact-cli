#!/usr/bin/env bash
# Pre-commit quality checks for specfact-cli (layout parity with specfact-cli-modules).
#
# Pre-commit buffers output until each hook finishes; split into subcommands so each stage
# completes and prints before the next hook starts (see .pre-commit-config.yaml).
#
# Subcommands: block1-format | block1-yaml | block1-markdown-fix | block1-markdown-lint |
#              block1-workflows | block1-lint | block2 | all
#
# Note: specfact-cli has no packages/ tree; there is no bundle-import hook (see
# specfact-cli-modules check-bundle-imports). Module signature verification is a separate
# pre-commit hook in .pre-commit-config.yaml, matching the modules repo.

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}$*${NC}" >&2; }
success() { echo -e "${GREEN}$*${NC}" >&2; }
warn() { echo -e "${YELLOW}$*${NC}" >&2; }
error() { echo -e "${RED}$*${NC}" >&2; }

print_block1_overview() {
  echo "" >&2
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
  echo "  specfact-cli pre-commit — Block 1: quality checks" >&2
  echo "    format → YAML (staged) → Markdown fix/lint (staged) → workflows (staged) → lint (staged Python)" >&2
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
  echo "" >&2
}

print_block2_overview() {
  echo "" >&2
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
  echo "  specfact-cli pre-commit — Block 2: Requirements evidence + delivery checks" >&2
  echo "    1/3  Requirements evidence (staged active OpenSpec changes)" >&2
  echo "    2/3  code review gate (staged Python under src/, scripts/, tools/, tests/, openspec/changes/)" >&2
  echo "    3/3  contract-first tests (contract-test-status → hatch run contract-test-contracts)" >&2
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
  echo "" >&2
}

# Include deletions (D): a commit that only removes paths must still be visible here so
# check_safe_change() and Block 2 logic do not treat it as an empty / "safe" commit.
staged_files() {
  git diff --cached --name-only --diff-filter=ACMRD
}

staged_evidence_paths() {
  local status source_path destination_path
  while IFS= read -r -d '' status; do
    if ! IFS= read -r -d '' source_path; then
      error "Unable to read staged source path for ${status}"
      return 1
    fi
    printf '%s\0' "${source_path}"
    case "${status}" in
      R*|C*)
        if ! IFS= read -r -d '' destination_path; then
          error "Unable to read staged destination path for ${status}"
          return 1
        fi
        printf '%s\0' "${destination_path}"
        ;;
    esac
  done < <(git diff --cached --name-status -z --find-renames --diff-filter=ACMRD)
}

has_staged_yaml() {
  local line
  while IFS= read -r line || [[ -n "${line}" ]]; do
    [[ -z "${line}" ]] && continue
    if [[ "${line}" =~ \.(yaml|yml)$ ]]; then
      return 0
    fi
  done < <(staged_files)
  return 1
}

has_staged_workflows() {
  local line
  while IFS= read -r line || [[ -n "${line}" ]]; do
    [[ -z "${line}" ]] && continue
    if [[ "${line}" =~ ^\.github/workflows/.*\.ya?ml$ ]]; then
      return 0
    fi
  done < <(staged_files)
  return 1
}

has_staged_markdown() {
  local line
  while IFS= read -r line || [[ -n "${line}" ]]; do
    [[ -z "${line}" ]] && continue
    if [[ "${line}" =~ \.(md|mdc)$ ]] && [[ -f "${line}" ]]; then
      return 0
    fi
  done < <(staged_files)
  return 1
}

has_staged_python() {
  local line
  while IFS= read -r line || [[ -n "${line}" ]]; do
    [[ -z "${line}" ]] && continue
    if [[ "${line}" =~ \.(py|pyi)$ ]]; then
      return 0
    fi
  done < <(staged_files)
  return 1
}

staged_python_files() {
  local line
  while IFS= read -r line || [[ -n "${line}" ]]; do
    [[ -z "${line}" ]] && continue
    if [[ "${line}" =~ \.(py|pyi)$ ]] && [[ -f "${line}" ]]; then
      printf '%s\n' "${line}"
    fi
  done < <(staged_files)
}

staged_markdown_files() {
  local line
  while IFS= read -r line || [[ -n "${line}" ]]; do
    [[ -z "${line}" ]] && continue
    if [[ "${line}" =~ \.(md|mdc)$ ]] && [[ -f "${line}" ]]; then
      printf '%s\n' "${line}"
    fi
  done < <(staged_files)
}

# Paths eligible for the code review gate (parity with modules: scoped prefixes; non-Python filtered by pre_commit_code_review.py).
staged_review_gate_files() {
  local line
  while IFS= read -r line || [[ -n "${line}" ]]; do
    [[ -z "${line}" ]] && continue
    case "${line}" in
      */TDD_EVIDENCE.md|TDD_EVIDENCE.md) continue ;;
      src/*|scripts/*|tools/*|tests/*|openspec/changes/*)
        # Deletions have no working-tree file; skip them for the review runner (contract
        # tests still run because check_safe_change sees the deleted path).
        [[ -f "${line}" ]] || continue
        printf '%s\n' "${line}"
        ;;
    esac
  done < <(staged_files)
}

fail_if_markdown_has_unstaged_hunks() {
  local file
  while IFS= read -r file || [[ -n "${file}" ]]; do
    [[ -z "${file}" ]] && continue
    if ! git diff --quiet -- "${file}"; then
      error "❌ Cannot auto-fix Markdown with unstaged hunks: ${file}"
      warn "💡 Stage the full file or stash/revert the unstaged Markdown changes before commit"
      exit 1
    fi
  done < <(staged_markdown_files)
}

fail_if_generated_artifacts_have_unstaged_hunks() {
  local file
  for file in llms.txt docs/reference/commands.generated.json docs/reference/commands.generated.md; do
    [[ -f "${file}" ]] || continue
    if ! git diff --quiet -- "${file}"; then
      error "❌ Cannot stage generated command artifacts with unstaged hunks: ${file}"
      warn "💡 Stage the full file or stash/revert the unstaged generated-artifact changes before commit"
      exit 1
    fi
  done
}

check_safe_change() {
  local other_changes=0
  local saw_any=false
  local file
  while IFS= read -r file || [[ -n "${file}" ]]; do
    [[ -z "${file}" ]] && continue
    saw_any=true
    case "${file}" in
      src/__init__.py|src/specfact_cli/__init__.py) ;;
      CHANGELOG.md|README.md|.pre-commit-config.yaml) ;;
      tools/smart_test_coverage.py|tools/functional_coverage_analyzer.py) ;;
      openspec/changes/*)
        other_changes=$((other_changes + 1))
        ;;
      *.md|*.mdc|*.rst|*.txt|*.json|*.yaml|*.yml) ;;
      docs/*|papers/*|presentations/*|images/*) ;;
      .github/workflows/*) ;;
      *)
        other_changes=$((other_changes + 1))
        ;;
    esac
  done < <(staged_files)

  if [[ "${saw_any}" == false ]]; then
    return 0
  fi
  [[ "${other_changes}" -eq 0 ]]
}

run_version_sources_check_if_needed() {
  local version_paths=("pyproject.toml" "setup.py" "src/__init__.py" "src/specfact_cli/__init__.py")
  local hit=0
  local f
  local p
  while IFS= read -r f || [[ -n "${f}" ]]; do
    [[ -z "${f}" ]] && continue
    for p in "${version_paths[@]}"; do
      if [[ "${f}" == "${p}" ]]; then
        hit=1
        break
      fi
    done
    [[ "${hit}" -eq 1 ]] && break
  done < <(staged_files)
  if [[ "${hit}" -eq 0 ]]; then
    return 0
  fi
  info "📌 Version file(s) staged — verifying synchronized versions"
  if hatch run check-version-sources; then
    success "✅ Version sources are synchronized"
  else
    error "❌ Version mismatch across pyproject.toml, setup.py, src/__init__.py, src/specfact_cli/__init__.py"
    warn "💡 Run: hatch run check-version-sources"
    exit 1
  fi
}

run_module_signature_verification() {
  local root primary legacy chosen rel
  root=$(git rev-parse --show-toplevel 2>/dev/null || true)
  if [ -z "${root}" ]; then
    error "❌ Cannot resolve git repository root for module signature verification"
    exit 1
  fi
  primary="${root}/scripts/pre-commit-verify-modules.sh"
  legacy="${root}/scripts/pre-commit-verify-modules-signature.sh"
  chosen=""
  if [[ -f "${primary}" ]]; then
    chosen="${primary}"
    rel="scripts/pre-commit-verify-modules.sh"
  elif [[ -f "${legacy}" ]]; then
    chosen="${legacy}"
    rel="scripts/pre-commit-verify-modules-signature.sh (legacy entrypoint)"
  else
    error "❌ Missing module verify script: ${primary} and ${legacy} not found"
    exit 1
  fi
  info "📦 Module verify — running ${rel}"
  if bash "${chosen}"; then
    success "✅ Module signature/version verification passed (or skipped — no staged module tree changes)"
  else
    error "❌ Module signature/version verification failed (${rel})"
    warn "💡 On main use --require-signature; elsewhere CI signs after PR approval"
    exit 1
  fi
}

run_format_safety() {
  info "📦 Block 1 — format — running \`hatch run format\` (fails if working tree would change)"
  local before_unstaged after_unstaged before_ec after_ec
  before_ec=0
  before_unstaged=$(git diff --binary -- . 2>&1) || before_ec=$?
  if [[ "${before_ec}" -gt 1 ]]; then
    error "❌ git diff failed (cannot snapshot working tree before format; exit ${before_ec})"
    exit 1
  fi
  if hatch run format; then
    after_ec=0
    after_unstaged=$(git diff --binary -- . 2>&1) || after_ec=$?
    if [[ "${after_ec}" -gt 1 ]]; then
      error "❌ git diff failed (cannot snapshot working tree after format; exit ${after_ec})"
      exit 1
    fi
    if [ "${before_unstaged}" != "${after_unstaged}" ]; then
      error "❌ Formatter changed files. Review and re-stage before committing."
      warn "💡 Run: hatch run format && git add -A"
      exit 1
    fi
    success "✅ Block 1 — format passed"
  else
    error "❌ Block 1 — format failed"
    exit 1
  fi
}

run_yaml_lint_if_needed() {
  if has_staged_yaml; then
    info "📦 Block 1 — YAML — running \`hatch run yaml-lint\` (staged YAML detected)"
    if hatch run yaml-lint; then
      success "✅ Block 1 — YAML validation passed"
    else
      error "❌ Block 1 — YAML validation failed"
      exit 1
    fi
  else
    info "📦 Block 1 — YAML — skipped (no staged *.yaml / *.yml)"
  fi
}

run_markdown_autofix_if_needed() {
  if ! has_staged_markdown; then
    info "📦 Block 1 — Markdown fix — skipped (no staged *.md / *.mdc)"
    return
  fi
  info "📦 Block 1 — Markdown fix — attempting safe auto-fix"
  local md_files=()
  local line
  while IFS= read -r line || [[ -n "${line}" ]]; do
    [[ -z "${line}" ]] && continue
    md_files+=("${line}")
  done < <(staged_markdown_files)
  if ((${#md_files[@]} == 0)); then
    info "ℹ️  No staged markdown files resolved — skipping markdown auto-fix"
    return
  fi
  fail_if_markdown_has_unstaged_hunks
  if command -v markdownlint >/dev/null 2>&1; then
    if markdownlint --fix --config .markdownlint.json "${md_files[@]}"; then
      if ! git diff --quiet -- "${md_files[@]}"; then
        git add -- "${md_files[@]}"
      fi
      success "✅ Block 1 — Markdown auto-fix applied"
    else
      error "❌ Block 1 — Markdown auto-fix failed"
      exit 1
    fi
  else
    if npx --yes markdownlint-cli --fix --config .markdownlint.json "${md_files[@]}"; then
      if ! git diff --quiet -- "${md_files[@]}"; then
        git add -- "${md_files[@]}"
      fi
      success "✅ Block 1 — Markdown auto-fix applied (npx)"
    else
      error "❌ Block 1 — Markdown auto-fix failed (npx)"
      warn "💡 Install markdownlint-cli globally for faster hooks: npm i -g markdownlint-cli"
      exit 1
    fi
  fi
}

run_markdown_lint_if_needed() {
  if ! has_staged_markdown; then
    info "📦 Block 1 — Markdown lint — skipped (no staged *.md / *.mdc)"
    return
  fi
  info "📦 Block 1 — Markdown lint — running markdownlint"
  local md_files=()
  local line
  while IFS= read -r line || [[ -n "${line}" ]]; do
    [[ -z "${line}" ]] && continue
    md_files+=("${line}")
  done < <(staged_markdown_files)
  if ((${#md_files[@]} == 0)); then
    return
  fi
  if command -v markdownlint >/dev/null 2>&1; then
    if markdownlint --config .markdownlint.json "${md_files[@]}"; then
      success "✅ Block 1 — Markdown lint passed"
    else
      error "❌ Block 1 — Markdown lint failed"
      exit 1
    fi
  else
    if npx --yes markdownlint-cli --config .markdownlint.json "${md_files[@]}"; then
      success "✅ Block 1 — Markdown lint passed (npx)"
    else
      error "❌ Block 1 — Markdown lint failed (npx)"
      exit 1
    fi
  fi
}

run_workflow_lint_if_needed() {
  if has_staged_workflows; then
    info "📦 Block 1 — workflows — running \`hatch run lint-workflows\`"
    if hatch run lint-workflows; then
      success "✅ Block 1 — workflow lint passed"
    else
      error "❌ Block 1 — workflow lint failed"
      exit 1
    fi
  else
    info "📦 Block 1 — workflows — skipped (no staged .github/workflows/*.yml)"
  fi
}

run_lint_if_staged_python() {
  local lint_array=()
  if ! has_staged_python; then
    info "📦 Block 1 — lint — skipped (no staged *.py / *.pyi)"
    return 0
  fi
  while IFS= read -r line || [[ -n "${line}" ]]; do
    [[ -z "${line}" ]] && continue
    lint_array+=("${line}")
  done < <(staged_python_files)
  if [ ${#lint_array[@]} -eq 0 ]; then
    info "📦 Block 1 — lint — skipped (no existing staged *.py / *.pyi targets)"
    return 0
  fi
  info "📦 Block 1 — lint — running \`hatch run lint-changed\` on ${#lint_array[@]} staged Python path(s)"
  if hatch run lint-changed "${lint_array[@]}"; then
    success "✅ Block 1 — lint passed"
  else
    error "❌ Block 1 — lint failed"
    warn "💡 Run: hatch run lint-changed <paths> (local) or hatch run lint (full repo)"
    exit 1
  fi
}

staged_required_maturity() {
  local file maturity="planned"
  while IFS= read -r -d '' file; do
    case "${file}" in
      .github/*|ci/*|scripts/*|src/*|pyproject.toml|setup.py|uv.lock|requirements/ci/locked.txt)
        printf 'verified\n'
        return 0
        ;;
      tests/*) maturity="test-authored" ;;
    esac
  done < <(staged_evidence_paths)
  printf '%s\n' "${maturity}"
}

staged_planning_maturity() {
  # Pre-commit never runs the selected test plan or reconciles JUnit, so its
  # strongest truthful evidence is an accepted, executable test plan.
  case "$(staged_required_maturity)" in
    verified) printf "test-authored\n" ;;
    *) staged_required_maturity ;;
  esac
}

has_staged_requirements_evidence_scope() {
  local file
  while IFS= read -r -d '' file; do
    return 0
  done < <(staged_evidence_paths)
  return 1
}

staged_active_change_ids() {
  local file relative_path
  local -A change_ids=()
  while IFS= read -r -d '' file; do
    case "${file}" in
      openspec/changes/archive/*)
        ;;
      openspec/changes/*/*)
        relative_path="${file#openspec/changes/}"
        change_ids["${relative_path%%/*}"]=1
        ;;
    esac
  done < <(staged_evidence_paths)
  if [[ ${#change_ids[@]} -gt 0 ]]; then
    printf '%s\n' "${!change_ids[@]}" | sort
  fi
}

run_requirements_evidence_gate() {
  local report_dir=".specfact/reports/requirements-evidence"
  local json_report="${report_dir}/requirements-evidence.json"
  local markdown_report="${report_dir}/requirements-evidence.md"
  local plan_report="${report_dir}/requirements-evidence-plan.json"
  local required_maturity
  local review_evidence=""
  local selected_change=""
  local -a staged_change_ids=()
  local -a review_evidence_candidates=()
  local -a evidence_arguments=()

  if ! has_staged_requirements_evidence_scope; then
    info "📦 Block 2 — Requirements evidence — skipped (no staged path)"
    return 0
  fi

  mkdir -p "${report_dir}"
  rm -f "${json_report}" "${markdown_report}" "${plan_report}"
  required_maturity="$(staged_planning_maturity)"
  if [[ "${required_maturity}" != "planned" ]]; then
    mapfile -t staged_change_ids < <(staged_active_change_ids)
    if [[ ${#staged_change_ids[@]} -gt 1 ]]; then
      error "❌ Block 2 — Staged Requirements evidence spans multiple active changes"
      exit 1
    elif [[ ${#staged_change_ids[@]} -eq 1 ]]; then
      selected_change="${staged_change_ids[0]}"
      review_evidence="openspec/changes/${selected_change}/requirements-proof/review-evidence.json"
      if [[ ! -f "${review_evidence}" ]]; then
        error "❌ Block 2 — Staged change ${selected_change} has no review-evidence record for ${required_maturity} planning"
        exit 1
      fi
    else
      while IFS= read -r candidate || [[ -n "${candidate}" ]]; do
        [[ -z "${candidate}" ]] && continue
        review_evidence_candidates+=("${candidate}")
      done < <(find openspec/changes -path 'openspec/changes/archive' -prune -o -path '*/requirements-proof/review-evidence.json' -type f -print | sort)
      if [[ ${#review_evidence_candidates[@]} -ne 1 ]]; then
        error "❌ Block 2 — Requirements evidence needs exactly one active review-evidence record for ${required_maturity} planning"
        exit 1
      fi
      review_evidence="${review_evidence_candidates[0]}"
    fi
  fi
  evidence_arguments=(
    --repo-root .
    --staged
    --required-maturity "${required_maturity}"
    --output "${json_report}"
    --summary "${markdown_report}"
  )
  if [[ -n "${review_evidence}" ]]; then
    evidence_arguments+=(--review-evidence "${review_evidence}" --plan-output "${plan_report}")
  fi
  info "📦 Block 2 — Requirements evidence — running released pinned fixture"
  if hatch run python scripts/requirements_evidence_delivery_gate.py \
    "${evidence_arguments[@]}"; then
    if [[ ! -s "${json_report}" || ! -s "${markdown_report}" ]]; then
      error "❌ Block 2 — Requirements evidence did not produce both remediation reports"
      exit 1
    fi
    if [[ -n "${review_evidence}" && ! -s "${plan_report}" ]]; then
      error "❌ Block 2 — Requirements evidence did not produce the required test plan"
      exit 1
    fi
    success "✅ Block 2 — Requirements evidence passed (${json_report}; ${markdown_report})"
  else
    error "❌ Block 2 — Requirements evidence failed"
    if [[ -s "${json_report}" && -s "${markdown_report}" ]]; then
      warn "💡 Review ${json_report} and ${markdown_report}; set SPECFACT_MODULES_REPO to the checkout pinned in ci/module-fixture.lock.json."
    else
      warn "💡 Requirements evidence failed before diagnostic reports could be written; inspect the command output and fixture checkout."
    fi
    exit 1
  fi
}

run_code_review_gate() {
  local review_array=()
  while IFS= read -r line || [[ -n "${line}" ]]; do
    [[ -z "${line}" ]] && continue
    review_array+=("${line}")
  done < <(staged_review_gate_files)

  if [ ${#review_array[@]} -eq 0 ]; then
    info "📦 Block 2 — code review — skipped (no staged paths under src/, scripts/, tools/, tests/, or openspec/changes/)"
    return
  fi

  info "📦 Block 2 — code review — running \`hatch run python scripts/pre_commit_code_review.py\` (${#review_array[@]} path(s))"
  if hatch run python scripts/pre_commit_code_review.py "${review_array[@]}"; then
    success "✅ Block 2 — code review gate passed"
  else
    error "❌ Block 2 — code review gate failed"
    warn "💡 Fix severity=error review findings (see .specfact/code-review.json) or run: hatch run python scripts/pre_commit_code_review.py <paths>"
    exit 1
  fi
}

run_command_overview_validation_gate() {
  local hit=0
  local file
  while IFS= read -r file || [[ -n "${file}" ]]; do
    [[ -z "${file}" ]] && continue
    case "${file}" in
      src/*|docs/*|.github/*|resources/*|scripts/check-docs-commands.py|scripts/check-command-contract.py|scripts/check-documentation-accountability.py|scripts/generate-command-overview.py|README.md|llms.txt|docs/reference/commands.generated.*)
        hit=1
        break
        ;;
    esac
  done < <(staged_files)
  if [[ "${hit}" -eq 0 ]]; then
    return 0
  fi
  info "📦 Block 2 — command overview — regenerating current AI command artifacts"
  if hatch run generate-command-overview; then
    fail_if_generated_artifacts_have_unstaged_hunks
    git add -- llms.txt docs/reference/commands.generated.json docs/reference/commands.generated.md
    success "✅ Command overview artifacts regenerated and staged"
  else
    error "❌ Command overview generation failed"
    exit 1
  fi
  info "📦 Block 2 — command overview — running \`hatch run check-command-overview\`"
  if hatch run check-command-overview; then
    success "✅ Command overview validation passed"
  else
    error "❌ Command overview validation failed"
    warn "💡 Run: hatch run generate-command-overview"
    exit 1
  fi
  info "📦 Block 2 — command contract — running \`hatch run check-command-contract\`"
  if hatch run check-command-contract; then
    success "✅ Generated command contract validation passed"
  else
    error "❌ Generated command contract validation failed"
    warn "💡 Run: hatch run check-command-contract"
    exit 1
  fi
  info "📦 Block 2 — docs commands — running \`hatch run check-docs-commands\`"
  if hatch run check-docs-commands; then
    success "✅ Docs command validation passed"
  else
    error "❌ Docs command validation failed"
    warn "💡 Fix stale command examples or regenerate the command overview if the CLI changed"
    exit 1
  fi
  info "📦 Block 2 — documentation accountability — running \`hatch run check-documentation-accountability\`"
  if hatch run check-documentation-accountability; then
    success "✅ Documentation accountability validation passed"
  else
    error "❌ Documentation accountability validation failed"
    exit 1
  fi
}

run_contract_tests_visible() {
  info "📦 Block 2 — contract tests — running \`hatch run contract-test-status\`"
  # Discard status-check output: transient failures (missing optional deps, environment noise) should
  # not alarm the user; we fall through to scoped contract checks that surface real failures quickly.
  if hatch run contract-test-status >/dev/null 2>&1; then
    success "✅ Block 2 — contract tests — skipped (contract-test-status: no input changes)"
  else
    info "📦 Block 2 — contract tests — running \`hatch run contract-test-contracts\`"
    if hatch run contract-test-contracts; then
      success "✅ Block 2 — contract-first tests passed"
      warn "💡 CI may still run the full quality matrix"
    else
      error "❌ Block 2 — contract-first tests failed"
      warn "💡 Run: hatch run contract-test-contracts"
      exit 1
    fi
  fi
}

check_contract_script_exists() {
  if [[ ! -f "tools/contract_first_smart_test.py" ]]; then
    error "❌ Contract-first test script not found. Please run: hatch run contract-test-full"
    exit 1
  fi
}

run_block1_format() {
  warn "🔍 specfact-cli pre-commit — Block 1 — hook: format"
  print_block1_overview
  run_format_safety
}

run_block1_yaml() {
  warn "🔍 specfact-cli pre-commit — Block 1 — hook: YAML"
  run_yaml_lint_if_needed
}

run_block1_markdown_fix() {
  warn "🔍 specfact-cli pre-commit — Block 1 — hook: Markdown auto-fix"
  run_markdown_autofix_if_needed
}

run_block1_markdown_lint() {
  warn "🔍 specfact-cli pre-commit — Block 1 — hook: Markdown lint"
  run_markdown_lint_if_needed
}

run_block1_workflows() {
  warn "🔍 specfact-cli pre-commit — Block 1 — hook: workflow lint"
  run_workflow_lint_if_needed
}

run_block1_lint() {
  warn "🔍 specfact-cli pre-commit — Block 1 — hook: lint"
  run_lint_if_staged_python
}

run_block2() {
  warn "🔍 specfact-cli pre-commit — Block 2 — hook: review + contract tests"
  print_block2_overview
  run_requirements_evidence_gate
  run_command_overview_validation_gate
  if check_safe_change; then
    success "✅ Safe change detected — skipping Block 2 (code review + contract tests)"
    info "💡 Only docs (incl. *.mdc), workflow, version files, or allowlisted infra changed"
    exit 0
  fi
  run_code_review_gate
  check_contract_script_exists
  run_contract_tests_visible
}

run_all() {
  warn "🔍 Running full specfact-cli pre-commit pipeline (\`all\` — manual or CI)"
  print_block1_overview
  run_module_signature_verification
  run_version_sources_check_if_needed
  run_format_safety
  run_yaml_lint_if_needed
  run_markdown_autofix_if_needed
  run_markdown_lint_if_needed
  run_workflow_lint_if_needed
  run_lint_if_staged_python
  success "✅ Block 1 complete (all stages passed or skipped as expected)"
  print_block2_overview
  run_requirements_evidence_gate
  run_command_overview_validation_gate
  if check_safe_change; then
    success "✅ Safe change detected — skipping Block 2 (code review + contract tests)"
    info "💡 Only docs (incl. *.mdc), workflow, version files, or allowlisted infra changed"
    exit 0
  fi
  run_code_review_gate
  check_contract_script_exists
  run_contract_tests_visible
}

usage_error() {
  error "Usage: $0 {block1-format|block1-yaml|block1-markdown-fix|block1-markdown-lint|block1-workflows|block1-lint|block2|all} (also: -h | --help | help)"
  exit 2
}

show_help() {
  echo "Usage: $0 {block1-format|block1-yaml|block1-markdown-fix|block1-markdown-lint|block1-workflows|block1-lint|block2|all}" >&2
  echo "Help aliases: -h, --help, help" >&2
  exit 0
}

main() {
  case "${1:-all}" in
    block1-format)
      run_block1_format
      ;;
    block1-yaml)
      run_block1_yaml
      ;;
    block1-markdown-fix)
      run_block1_markdown_fix
      ;;
    block1-markdown-lint)
      run_block1_markdown_lint
      ;;
    block1-workflows)
      run_block1_workflows
      ;;
    block1-lint)
      run_block1_lint
      ;;
    block2)
      run_block2
      ;;
    all)
      run_all
      ;;
    -h|--help|help)
      show_help
      ;;
    *)
      usage_error
      ;;
  esac
}

main "$@"
