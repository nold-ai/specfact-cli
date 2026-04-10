# CI Docs Sync Check - Implementation Tasks

## TDD / SDD order (enforced)

Per config.yaml and design.md, this change follows strict TDD-first ordering:

1. Spec deltas first (already created in specs/)
2. Tests second (expect failure initially)  
3. Code last (implement to pass tests)

Do not implement production code until tests exist and have been run (expecting failure).

---

## 1. Create git worktree for this change

- [ ] 1.1 Fetch latest and create a worktree with a new branch from `origin/dev`
  - [ ] 1.1.1 `git fetch origin`
  - [ ] 1.1.2 `git worktree add ../specfact-cli-worktrees/feature/ci-docs-sync-check -b feature/ci-docs-sync-check origin/dev`
  - [ ] 1.1.3 Change into the worktree: `cd ../specfact-cli-worktrees/feature/ci-docs-sync-check`
  - [ ] 1.1.4 Create a virtual environment: `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
  - [ ] 1.1.5 `git branch --show-current` (verify correct branch)

## 2. Test Infrastructure Setup

- [ ] 2.1 Create test directory structure
  - [ ] 2.1.1 `mkdir -p tests/unit/scripts/test_docs_sync`
  - [ ] 2.1.2 `mkdir -p tests/integration/scripts/test_docs_sync`

- [ ] 2.2 Add test dependencies
  - [ ] 2.2.1 Ensure PyYAML is available: `pip install pyyaml`
  - [ ] 2.2.2 Add any additional test dependencies

## 3. Test Implementation (TDD - Create Tests First)

### 3.1 Sync Algorithm Tests

- [ ] 3.1.1 Create `tests/unit/scripts/test_docs_sync/test_algorithm.py`
  - [ ] 3.1.1.1 Test change detection with git diff
  - [ ] 3.1.1.2 Test glob pattern matching
  - [ ] 3.1.1.3 Test stale documentation identification
  - [ ] 3.1.1.4 Test exempt document handling
  - [ ] 3.1.1.5 Test error reporting format

- [ ] 3.1.2 Run tests and expect failure (record in TDD_EVIDENCE.md)
  - [ ] 3.1.2.1 `pytest tests/unit/scripts/test_docs_sync/test_algorithm.py -v`
  - [ ] 3.1.2.2 Capture failure output in `openspec/changes/ci-docs-sync-check/TDD_EVIDENCE.md`

### 3.2 GitHub Workflow Tests

- [ ] 3.2.1 Create `tests/unit/scripts/test_docs_sync/test_workflow.py`
  - [ ] 3.2.1.1 Test workflow file validation
  - [ ] 3.2.1.2 Test workflow step execution
  - [ ] 3.2.1.3 Test error handling scenarios

- [ ] 3.2.2 Run tests and expect failure (record in TDD_EVIDENCE.md)
  - [ ] 3.2.2.1 `pytest tests/unit/scripts/test_docs_sync/test_workflow.py -v`
  - [ ] 3.2.2.2 Capture failure output

### 3.3 Integration Tests

- [ ] 3.3.1 Create `tests/integration/scripts/test_docs_sync/test_integration.py`
  - [ ] 3.3.1.1 Test end-to-end sync check workflow
  - [ ] 3.3.1.2 Test GitHub Actions integration
  - [ ] 3.3.1.3 Test performance with large changesets

- [ ] 3.3.2 Run integration tests and expect failure (record in TDD_EVIDENCE.md)
  - [ ] 3.3.2.1 `pytest tests/integration/scripts/test_docs_sync/ -v`
  - [ ] 3.3.2.2 Capture failure output

## 4. Implementation (Create Code to Pass Tests)

### 4.1 Sync Algorithm Implementation

- [ ] 4.1.1 Create `scripts/check-docs-sync.py`
  - [ ] 4.1.1.1 Implement `get_changed_files(base, head)` function with `@icontract` and `@beartype`
  - [ ] 4.1.1.2 Implement `parse_frontmatter(path)` function
  - [ ] 4.1.1.3 Implement `detect_stale_docs(changed_files)` function
  - [ ] 4.1.1.4 Implement main sync check algorithm

### 4.2 GitHub Workflow Implementation

- [ ] 4.2.1 Create `.github/workflows/docs-sync.yml`
  - [ ] 4.2.1.1 Implement checkout step with fetch-depth: 0
  - [ ] 4.2.1.2 Implement Python setup step
  - [ ] 4.2.1.3 Implement docs sync check step
  - [ ] 4.2.1.4 Add proper error handling and output formatting

### 4.3 Command-Line Interface

- [ ] 4.3.1 Add argument parsing to `check-docs-sync.py`
  - [ ] 4.3.1.1 Implement `--base` and `--head` arguments
  - [ ] 4.3.1.2 Add help text and usage examples

### 4.4 Test Execution and Evidence

- [ ] 4.4.1 Run all tests and verify they now pass
  - [ ] 4.4.1.1 `pytest tests/unit/scripts/test_docs_sync/ -v`
  - [ ] 4.4.1.2 `pytest tests/integration/scripts/test_docs_sync/ -v`
  - [ ] 4.4.1.3 Capture passing results in `TDD_EVIDENCE.md`

## 5. Quality Gates and Validation

### 5.1 Code Quality Checks

- [ ] 5.1.1 Run formatting: `hatch run format`
- [ ] 5.1.2 Run type checking: `hatch run type-check`
- [ ] 5.1.3 Run linting: `hatch run lint`
- [ ] 5.1.4 Fix any issues found

### 5.2 Contract Validation

- [ ] 5.2.1 Run contract tests: `hatch run contract-test`
- [ ] 5.2.2 Ensure all `@icontract` and `@beartype` decorators work correctly

### 5.3 OpenSpec Validation

- [ ] 5.3.1 Run `openspec validate ci-docs-sync-check --strict`
- [ ] 5.3.2 Fix any validation issues

## 6. Documentation Updates

### 6.1 CI Workflow Documentation

- [ ] 6.1.1 Create `docs/contributing/ci-docs-sync.md`
  - [ ] 6.1.1.1 Document CI workflow structure
  - [ ] 6.1.1.2 Explain sync algorithm behavior
  - [ ] 6.1.1.3 Provide troubleshooting guide

### 6.2 Developer Guidance

- [ ] 6.2.1 Add CI integration section to contributing docs
  - [ ] 6.2.1.1 Explain how CI enforcement works
  - [ ] 6.2.1.2 Document exemption process
  - [ ] 6.2.1.3 Provide error resolution examples

### 6.3 Update README

- [ ] 6.3.1 Update README with CI workflow information
- [ ] 6.3.2 Add badges for docs sync status

## 7. GitHub Integration

### 7.1 Branch Protection Configuration

- [ ] 7.1.1 Update branch protection settings
  - [ ] 7.1.1.1 Make docs sync check required status check
  - [ ] 7.1.1.2 Configure for main and develop branches

### 7.2 Test Workflow Execution

- [ ] 7.2.1 Test workflow on sample PR
  - [ ] 7.2.1.1 Create test PR with documentation changes
  - [ ] 7.2.1.2 Verify workflow executes correctly
  - [ ] 7.2.1.3 Test both success and failure scenarios

## 8. Sample Implementation and Testing

### 8.1 Test with Sample Repository

- [ ] 8.1.1 Create test repository with sample docs
- [ ] 8.1.2 Add frontmatter to sample files
- [ ] 8.1.3 Test sync algorithm with various scenarios

### 8.2 Test Error Scenarios

- [ ] 8.2.1 Create scenarios with stale documentation
- [ ] 8.2.2 Test workflow error detection
- [ ] 8.2.3 Verify error messages are actionable

## 9. Create GitHub Issue and PR

### 9.1 Create GitHub Issue

- [ ] 9.1.1 Create issue in nold-ai/specfact-cli
  - [ ] 9.1.1.1 Title: `[Change] CI Docs Sync Check`
  - [ ] 9.1.1.2 Labels: `enhancement`, `change-proposal`, `documentation`, `quality`, `ci`
  - [ ] 9.1.1.3 Body: Summary from proposal.md
  - [ ] 9.1.1.4 Link to parent epic: `feature/docs-sync-epic`
  - [ ] 9.1.1.5 Note dependency on `doc-frontmatter-schema` change

### 9.2 Create Pull Request

- [ ] 9.2.1 Prepare commit with all changes
  - [ ] 9.2.1.1 `git add .`
  - [ ] 9.2.1.2 `git commit -m "feat: add CI docs sync check"`
  - [ ] 9.2.1.3 `git push -u origin feature/ci-docs-sync-check`

- [ ] 9.2.2 Create PR using GitHub CLI
  - [ ] 9.2.2.1 `gh pr create --repo nold-ai/specfact-cli --base dev --head feature/ci-docs-sync-check`
  - [ ] 9.2.2.2 Use PR template with OpenSpec change ID
  - [ ] 9.2.2.3 Link to GitHub issue and dependency

- [ ] 9.2.3 Add to project board
  - [ ] 9.2.3.1 `gh project item-add 1 --owner nold-ai --url <PR_URL>`

## 10. Post-merge cleanup (after PR is merged)

- [ ] 10.1 Return to primary checkout: `cd .../specfact-cli`
- [ ] 10.2 `git fetch origin`
- [ ] 10.3 `git worktree remove ../specfact-cli-worktrees/feature/ci-docs-sync-check`
- [ ] 10.4 `git branch -d feature/ci-docs-sync-check`
- [ ] 10.5 `git worktree prune`
- [ ] 10.6 (Optional) `git push origin --delete feature/ci-docs-sync-check`
