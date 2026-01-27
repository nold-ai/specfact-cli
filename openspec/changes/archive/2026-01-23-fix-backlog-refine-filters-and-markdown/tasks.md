# Tasks: Fix backlog refine filters, limits, and ADO rendering

## 1. Git Workflow

- [x] 1.1.1 Ensure we're on dev and up to date: `git checkout dev && git pull origin dev`
- [x] 1.1.2 Create branch with issue link (if issue exists): `gh issue develop <issue-number> --repo nold-ai/specfact-cli --name bugfix/fix-backlog-refine-filters-and-markdown --checkout`
- [x] 1.1.3 Or create branch without issue link: `git checkout -b bugfix/fix-backlog-refine-filters-and-markdown`
- [x] 1.1.4 Verify branch: `git branch --show-current`

## 2. OpenSpec Updates

- [x] 2.1 Update `openspec/changes/fix-backlog-refine-filters-and-markdown/specs/backlog-refinement/spec.md` with limit/cancel/filter scenarios
- [x] 2.2 Update `openspec/changes/fix-backlog-refine-filters-and-markdown/specs/backlog-adapter/spec.md` with case-insensitive and identity matching semantics
- [x] 2.3 Update `openspec/changes/fix-backlog-refine-filters-and-markdown/specs/format-abstraction/spec.md` with provider-specific rendering requirements
- [x] 2.4 Run OpenSpec validation: `openspec validate fix-backlog-refine-filters-and-markdown --strict` (passed)

## 3. CLI Batch Control & Prompt Flow

- [x] 3.1 Add `--limit` option to `specfact backlog refine` and pass through `_fetch_backlog_items`
- [x] 3.2 Ensure `_fetch_backlog_items` respects `limit` deterministically (adapter query limit where possible, slice after filtering)
- [x] 3.3 Add prompt sentinels for `:skip`, `:quit`, `:abort` to exit cleanly and print summary
- [x] 3.4 Ensure cancel path does not write any backlog updates and returns non-error exit code

## 4. Filter Normalization

- [x] 4.1 Add shared normalization helper for state/assignee/sprint comparisons (lowercase, trim, collapse spaces)
- [x] 4.2 Apply case-insensitive state/assignee filtering in ADO and GitHub adapters
- [x] 4.3 Implement ADO sprint filter rules: full iteration path matching, ambiguity detection for name-only values, and explicit error message with candidates
- [x] 4.4 Add `--ado-team` option and default team fallback (project name) for iteration lookup
- [x] 4.5 Implement current iteration lookup via ADO team iterations API (`$timeframe=current`) when `--sprint` is omitted
- [x] 4.6 Update BacklogFilters (if needed) to carry normalized values or new `limit` field

## 5. ADO Markdown Rendering

- [x] 5.1 Update ADO `update_backlog_item` to set `/multilineFieldsFormat/System.Description` to `Markdown`
- [x] 5.2 Add Markdown → HTML fallback rendering when ADO rejects Markdown format
- [x] 5.3 Store render metadata in `provider_fields` for round-trip (e.g., original markdown, render format)

## 6. Documentation & Prompts

- [x] 6.1 Update CLI help/docs to document `--limit`, sprint path rules, and assignee formats
- [x] 6.2 Update AI prompt template `specfact.backlog-refine.md` with new options and examples

## 7. Startup Checks

- [x] 7.1 Create `startup_checks.py` module with template validation and version checking utilities
- [x] 7.2 Implement `check_ide_templates()` to compare IDE template files with bundled templates (using modification time heuristic)
- [x] 7.3 Implement `check_pypi_version()` to check for available CLI updates (minor/major/patch) from PyPI
- [x] 7.4 Implement `print_startup_checks()` to display warnings for outdated templates and available updates
- [x] 7.5 Integrate startup checks into `cli.py` main entry point (run on command execution, skip for help/version)
- [x] 7.6 Add graceful error handling with `contextlib.suppress` to prevent startup check failures from crashing CLI

## 8. Tests

- [x] 8.1 Unit tests for filter normalization (state/assignee/sprint) - Created `test_filter_normalization.py` with comprehensive tests
- [x] 8.2 Unit tests for ADO sprint path disambiguation and error messaging - Added to `test_ado_backlog_adapter.py`
- [x] 8.3 Integration test for ADO refinement writeback with Markdown rendering - Created `test_ado_markdown_rendering.py` (4 tests, all passing)
- [x] 8.4 E2E test for `specfact backlog refine --limit` and cancel flow - Created `test_backlog_refine_limit_and_cancel.py` (7 tests, all passing)
- [x] 8.5 Unit tests for `startup_checks` module - Created `test_startup_checks.py` with 24 comprehensive tests (all passing)
- [x] 8.6 Integration tests for startup checks in CLI - Created `test_startup_checks_integration.py` with integration tests

## 8. Quality Gates

- [x] 8.1 Run formatting: `hatch run format` (passed - 5 files reformatted)
- [x] 8.2 Run linting: `hatch run lint` (passed - only pre-existing warnings)
- [x] 8.3 Run type checking: `hatch run type-check` (passed - only pre-existing warnings)
- [x] 8.4 Run contract tests: `hatch run contract-test` (356 passed, 3 pre-existing failures unrelated to changes)
- [x] 8.5 Run smart tests: `hatch run smart-test-folder` (passed - no unit tests needed for all files, tests exist for modified files)
- [x] 8.6 Re-run OpenSpec validation: `openspec validate fix-backlog-refine-filters-and-markdown --strict` (passed)

## 10. Pull Request (specfact-cli)

- [x] 10.1 Ensure all changes are committed: `git add .`
- [x] 10.2 Commit with conventional message: `git commit -m "fix: backlog refine filters, ADO rendering, and add startup checks"`
- [x] 10.3 Push branch: `git push origin bugfix/fix-backlog-refine-filters-and-markdown`
- [x] 10.4 Create PR body file: `PR_BODY_FILE="/tmp/pr-body-fix-backlog-refine-filters-and-markdown.md"`
- [x] 10.5 Create PR: `gh pr create --repo nold-ai/specfact-cli --base dev --head bugfix/fix-backlog-refine-filters-and-markdown --title "fix: backlog refine filters, ADO rendering, and add startup checks" --body-file "$PR_BODY_FILE"`
- [x] 10.6 Link PR to issue and project if applicable
