# Doc Frontmatter Schema & Validation - Implementation Tasks

## TDD / SDD order (enforced)

Per config.yaml and design.md, this change follows strict TDD-first ordering:
1. Spec deltas first (already created in specs/)
2. Tests second (expect failure initially)
3. Code last (implement to pass tests)

Do not implement production code until tests exist and have been run (expecting failure).

---

## 1. Create git worktree for this change

- [x] 1.1 Fetch latest and create a worktree with a new branch from `origin/dev`
  - [x] 1.1.1 `git fetch origin`
  - [x] 1.1.2 `git worktree add ../specfact-cli-worktrees/feature/doc-frontmatter-schema -b feature/doc-frontmatter-schema origin/dev`
  - [x] 1.1.3 Change into the worktree: `cd ../specfact-cli-worktrees/feature/doc-frontmatter-schema`
  - [x] 1.1.4 Create a virtual environment: `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
  - [x] 1.1.5 `git branch --show-current` (verify correct branch)

## 2. Test Infrastructure Setup

- [x] 2.1 Create test directory structure
  - [x] 2.1.1 `mkdir -p tests/unit/scripts/test_doc_frontmatter`
  - [x] 2.1.2 `mkdir -p tests/integration/scripts/test_doc_frontmatter`

- [x] 2.2 Add test dependencies
  - [x] 2.2.1 Ensure PyYAML is in requirements: `pip install pyyaml`
  - [x] 2.2.2 Add to project dependencies if needed (PyYAML already in `pyproject.toml`)

## 3. Test Implementation (TDD - Create Tests First)

### 3.1 Frontmatter Schema Tests

- [x] 3.1.1 Create `tests/unit/scripts/test_doc_frontmatter/test_schema.py`
  - [x] 3.1.1.1 Test valid frontmatter parsing
  - [x] 3.1.1.2 Test missing required fields detection
  - [x] 3.1.1.3 Test owner identifier resolution
  - [x] 3.1.1.4 Test glob pattern validation
  - [x] 3.1.1.5 Test exemption handling

- [x] 3.1.2 Run tests and expect failure (record in TDD_EVIDENCE.md)
  - [x] 3.1.2.1 `pytest tests/unit/scripts/test_doc_frontmatter/test_schema.py -v`
  - [x] 3.1.2.2 Capture failure output in `openspec/changes/doc-frontmatter-schema/TDD_EVIDENCE.md`

### 3.2 Validation Logic Tests

- [x] 3.2.1 Create `tests/unit/scripts/test_doc_frontmatter/test_validation.py`
  - [x] 3.2.1.1 Test missing doc_owner detection
  - [x] 3.2.1.2 Test invalid owner resolution
  - [x] 3.2.1.3 Test fix hint generation
  - [x] 3.2.1.4 Test file discovery logic
  - [x] 3.2.1.5 Test exempt file handling

- [x] 3.2.2 Run tests and expect failure (record in TDD_EVIDENCE.md)
  - [x] 3.2.2.1 `pytest tests/unit/scripts/test_doc_frontmatter/test_validation.py -v`
  - [x] 3.2.2.2 Capture failure output

### 3.3 Integration Tests

- [x] 3.3.1 Create `tests/integration/scripts/test_doc_frontmatter/test_integration.py`
  - [x] 3.3.1.1 Test end-to-end validation workflow
  - [x] 3.3.1.2 Test multiple file scenarios
  - [x] 3.3.1.3 Test performance with many files

- [x] 3.3.2 Run integration tests and expect failure (record in TDD_EVIDENCE.md)
  - [x] 3.3.2.1 `pytest tests/integration/scripts/test_doc_frontmatter/ -v`
  - [x] 3.3.2.2 Capture failure output

## 4. Implementation (Create Code to Pass Tests)

### 4.1 Frontmatter Schema Implementation

- [x] 4.1.1 Create `scripts/check_doc_frontmatter.py`
  - [x] 4.1.1.1 Implement `parse_frontmatter()` function with `@icontract` and `@beartype`
  - [x] 4.1.1.2 Implement `extract_doc_owner()` function
  - [x] 4.1.1.3 Implement `resolve_owner()` function
  - [x] 4.1.1.4 Implement `validate_glob_patterns()` function
  - [x] 4.1.1.5 Implement `suggest_frontmatter()` function

### 4.2 Validation Logic Implementation

- [x] 4.2.1 Complete `check_doc_frontmatter.py` validation logic
  - [x] 4.2.1.1 Implement `get_all_md_files()` function
  - [x] 4.2.1.2 Implement `rg_missing_doc_owner()` function
  - [x] 4.2.1.3 Implement main validation loop
  - [x] 4.2.1.4 Implement error reporting with color coding

### 4.3 Command-Line Interface

- [x] 4.3.1 Add CLI with `--fix-hint` and `--all-docs` flags
  - [x] 4.3.1.1 Use Typer for CLI arguments (Rich-backed help via Typer)
  - [x] 4.3.1.2 Implement help text and usage examples

### 4.4 Test Execution and Evidence

- [x] 4.4.1 Run all tests and verify they now pass
  - [x] 4.4.1.1 `pytest tests/unit/scripts/test_doc_frontmatter/ -v`
  - [x] 4.4.1.2 `pytest tests/integration/scripts/test_doc_frontmatter/ -v`
  - [x] 4.4.1.3 Capture passing results in `TDD_EVIDENCE.md`

## 5. Quality Gates and Validation

### 5.1 Code Quality Checks

- [x] 5.1.1 Run formatting: `hatch run format`
- [x] 5.1.2 Run type checking: `hatch run type-check`
- [x] 5.1.3 Run linting: `hatch run lint`
- [x] 5.1.4 Fix any issues found

### 5.2 Contract Validation

- [x] 5.2.1 Run contract tests: `hatch run contract-test`
- [x] 5.2.2 Ensure all `@icontract` and `@beartype` decorators work correctly

### 5.3 OpenSpec Validation

- [x] 5.3.1 Run `openspec validate doc-frontmatter-schema --strict`
- [x] 5.3.2 Fix any validation issues

### 5.4 PR Orchestrator Parallelization Delta

- [x] 5.4.1 Extend spec/tests to cover PR orchestrator dependency parallelization
  - [x] 5.4.1.1 Add spec delta for independent CI job dependencies
  - [x] 5.4.1.2 Add workflow dependency tests in `tests/unit/specfact_cli/registry/test_signing_artifacts.py`
  - [x] 5.4.1.3 Run the new workflow dependency tests and record the expected failure in `TDD_EVIDENCE.md`
- [x] 5.4.2 Update `.github/workflows/pr-orchestrator.yml`
  - [x] 5.4.2.1 Remove unnecessary `tests` / downstream dependencies for jobs that do not consume test artifacts
  - [x] 5.4.2.2 Keep real artifact dependencies intact (`quality-gates`, main-branch packaging)
- [x] 5.4.3 Re-run workflow dependency tests and doc-frontmatter regression slice
  - [x] 5.4.3.1 Capture passing evidence in `TDD_EVIDENCE.md`

## 6. Documentation Updates

### 6.1 Frontmatter Schema Documentation

- [x] 6.1.1 Create `docs/contributing/docs-sync.md`
  - [x] 6.1.1.1 Document frontmatter schema with examples
  - [x] 6.1.1.2 Explain each field and its purpose
  - [x] 6.1.1.3 Provide common patterns and best practices

### 6.2 Validation Workflow Documentation

- [x] 6.2.1 Add validation workflow section to docs
  - [x] 6.2.1.1 Explain how validation works
  - [x] 6.2.1.2 Document error messages and fixes
  - [x] 6.2.1.3 Provide troubleshooting guide

### 6.3 Update Contributing Guidelines

- [x] 6.3.1 Update `CONTRIBUTING.md` with frontmatter requirements
- [x] 6.3.2 Add frontmatter section to documentation standards (`docs/contributing/docs-sync.md` is the canonical standards page for this rollout)

## 7. Pre-commit Integration

### 7.1 Update Pre-commit Configuration

- [x] 7.1.1 Modify `.pre-commit-config.yaml`
  - [x] 7.1.1.1 Add `check-doc-frontmatter` hook
  - [x] 7.1.1.2 Configure appropriate file patterns
  - [x] 7.1.1.3 Set `always_run: false`

### 7.2 Test Pre-commit Hook

- [x] 7.2.1 Run `pre-commit install` to install hooks
- [x] 7.2.2 Test hook with sample files
- [x] 7.2.3 Verify hook works correctly

## 8. Sample Implementation and Testing

### 8.1 Add Frontmatter to Sample Files

- [x] 8.1.1 Add frontmatter to 3-5 sample documentation files
- [x] 8.1.2 Test validation with sample files
- [x] 8.1.3 Verify no validation errors

### 8.2 Test Error Scenarios

- [x] 8.2.1 Create files with invalid frontmatter
- [x] 8.2.2 Test validation error detection
- [x] 8.2.3 Verify error messages are helpful

## 9. Create GitHub Issue and PR

### 9.1 Create GitHub Issue

- [x] 9.1.1 Create issue in nold-ai/specfact-cli
  - [x] 9.1.1.1 Title: `[Change] Doc Frontmatter Schema & Validation`
  - [x] 9.1.1.2 Labels: `enhancement`, `change-proposal`, `documentation`, `openspec` (repo-standard; `quality` not a label — use `QA` if needed later)
  - [x] 9.1.1.3 Body: Summary from proposal.md + OpenSpec paths + scope
  - [x] 9.1.1.4 Parent Feature: [#356](https://github.com/nold-ai/specfact-cli/issues/356) (linked in issue body; tracking comment on #356)
  - [x] 9.1.1.5 **Issue number**: [#461](https://github.com/nold-ai/specfact-cli/issues/461)

### 9.2 Create Pull Request

- [ ] 9.2.1 Prepare commit with all changes
  - [ ] 9.2.1.1 `git add .`
  - [ ] 9.2.1.2 `git commit -m "feat: add doc frontmatter schema and validation"`
  - [ ] 9.2.1.3 `git push -u origin feature/doc-frontmatter-schema`

- [ ] 9.2.2 Create PR using GitHub CLI
  - [ ] 9.2.2.1 `gh pr create --repo nold-ai/specfact-cli --base dev --head feature/doc-frontmatter-schema`
  - [ ] 9.2.2.2 Use PR template with OpenSpec change ID
  - [ ] 9.2.2.3 Link to GitHub issue

- [ ] 9.2.3 Add to project board
  - [ ] 9.2.3.1 `gh project item-add 1 --owner nold-ai --url <PR_URL>`

## 10. Post-merge cleanup (after PR is merged)

- [ ] 10.1 Return to primary checkout: `cd .../specfact-cli`
- [ ] 10.2 `git fetch origin`
- [ ] 10.3 `git worktree remove ../specfact-cli-worktrees/feature/doc-frontmatter-schema`
- [ ] 10.4 `git branch -d feature/doc-frontmatter-schema`
- [ ] 10.5 `git worktree prune`
- [ ] 10.6 (Optional) `git push origin --delete feature/doc-frontmatter-schema`
