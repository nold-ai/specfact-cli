# Tasks: Improve ADO backlog refine error logging and user-facing error UX

## 1. Create git branch from dev

- [ ] 1.1 Ensure we're on dev and up to date: `git checkout dev && git pull origin dev`
- [ ] 1.2 Create branch with Development link to issue: `gh issue develop 162 --repo nold-ai/specfact-cli --name bugfix/improve-ado-backlog-refine-error-logging --checkout`
- [ ] 1.3 Or create branch without issue link: `git checkout -b bugfix/improve-ado-backlog-refine-error-logging` (if no issue)
- [ ] 1.4 Verify branch was created: `git branch --show-current`

## 2. Verify spec deltas (SDD: specs first)

- [x] 2.1 Confirm `specs/api-error-diagnostics/spec.md` exists and is complete (ADDED requirements, Given/When/Then scenarios).
- [x] 2.2 Map scenarios to test cases: Debug log (response + patch paths), No sensitive data, Console message + hint on 400, Exception carries context, User message highlights failing field, Backlog refine / status / comment PATCH consistency, Non-JSON or oversized body handling.

## 3. Write tests from spec scenarios (TDD: tests second, expect failure)

- [x] 3.1 Add unit tests for the helper (from spec "Debug log contains response and patch paths"): given mock response (400, JSON body with `message`) and operations list, assert `debug_log_operation` is called with operation `ado_patch`, status `failed`, and `extra` containing `response_body` snippet and `patch_paths` when debug on; assert no call when debug off.
- [x] 3.2 Add unit test (from spec "No sensitive data in debug log"): response body containing token-like strings; assert logged snippet is redacted (e.g. via `LoggerSetup.redact_secrets` or equivalent check).
- [x] 3.3 Add unit test (from spec "Console shows ADO message and mapping hint on 400"): simulate 400 with body e.g. "TF51535: Cannot find field System.AcceptanceCriteria."; assert user-facing message contains "Cannot find field" (or equivalent) and hint text (e.g. "custom field mapping", "ado_custom.yaml" or documentation).
- [x] 3.4 Add unit test (from spec "Re-raised exception carries ADO context"): on PATCH failure, assert re-raised exception message or attached attribute includes ADO error message and mapping hint.
- [x] 3.5 Add unit test (from spec "User message highlights failing field when present"): ADO message contains field reference (e.g. "Cannot find field System.AcceptanceCriteria"); assert visible message quotes or emphasizes the field (e.g. "Field 'System.AcceptanceCriteria' not found") and hint follows.
- [x] 3.6 Add unit test (from spec "Non-JSON or oversized response body"): non-JSON body or very large body; assert no crash, response truncated (e.g. ~500–2000 chars), safe string used in log/user message.
- [x] 3.7 Add tests for consistency (from spec "Backlog refine body PATCH failure" / "Status update or comment PATCH failure"): assert same helper and user-message pattern is used in backlog-refine PATCH path, `_update_work_item_status`, `_update_work_item_body`, add-comment, and create-work-item PATCH paths (e.g. helper called with response and operations; console message before re-raise).
- [x] 3.8 Run tests and expect failure (no implementation yet): `hatch run smart-test-unit` (target tests for ado adapter); confirm failures are due to missing helper/behavior, not syntax.

## 4. Implement until tests pass (TDD: code last)

- [x] 4.1 Add helper in `src/specfact_cli/adapters/ado.py` (e.g. `_log_ado_patch_failure(response, operations, url, context="")`) that: parses response body (JSON `message` or `response.text[:500]`), extracts patch paths from `operations`, truncates/redacts snippet via `LoggerSetup.redact_secrets`, and when `is_debug_mode()` calls `debug_log_operation("ado_patch", url_redacted, "failed", error=message, extra={"response_body": snippet, "patch_paths": paths})`.
- [x] 4.2 Ensure `extra` values are safe: truncate response_body to ~1–2 KB; redact via `LoggerSetup.redact_secrets` before passing to `debug_log_operation`.
- [x] 4.3 Build user-facing string from ADO response: prefer `response.json().get("message", "")` or `response.text[:500]`; append hint "Check custom field mapping; see ado_custom.yaml or documentation."; when ADO message contains a field reference (e.g. "Cannot find field X"), quote or emphasize it (e.g. "Field 'X' not found") then append hint.
- [x] 4.4 In backlog-refine PATCH path (~line 3200): on `requests.HTTPError`, before any retry or re-raise, call the helper with `e.response`, `operations`, and URL; then print user message (`console.print("[bold red]✗[/bold red] ...")`) and optionally attach to exception; re-raise.
- [x] 4.5 In `_update_work_item_status` PATCH path: on `requests.RequestException`, call the helper (with response if available, patch_document paths) and surface ADO message + hint; `console.print` before re-raise.
- [x] 4.6 In `_update_work_item_body` PATCH path: same pattern (helper + user message + re-raise).
- [x] 4.7 In add-comment and create-work-item PATCH paths: same pattern for consistency.
- [x] 4.8 Optionally attach user message to exception (e.g. custom exception or `e.args`) so tests and upstream handlers can assert on it.
- [x] 4.9 Run unit tests until all pass: `hatch run smart-test-unit`; then `hatch run smart-test-folder`; fix implementation until green.

## 4b. OS-specific temp dir for exports (backlog refine and sync)

- [x] 4b.1 In `src/specfact_cli/commands/backlog_commands.py`: add `import tempfile`; replace hard-coded `/tmp` with `Path(tempfile.gettempdir())` for export and import default paths (lines ~716, ~767).
- [x] 4b.2 In `src/specfact_cli/sync/bridge_sync.py`: add `import tempfile`; replace all `Path(f"/tmp/specfact-proposal-...")` with `Path(tempfile.gettempdir()) / "specfact-proposal-..."` (export, sanitized, cleanup paths).
- [x] 4b.3 Update help strings in `backlog_commands.py` and `sync.py` to describe "system temporary directory" (or "<system-temp>/...") instead of `/tmp`.
- [x] 4b.4 Update docstring in `bridge_sync.py` for `tmp_file` default to mention system temp directory.

## 5. Quality gates

- [x] 5.1 Run format and type-check: `hatch run format`, `hatch run type-check`.
- [x] 5.2 Run contract test: `hatch run contract-test`.
- [x] 5.3 Run full test suite: `hatch run smart-test-full` (or `hatch test --cover -v`).
- [x] 5.4 Ensure all public APIs added or modified have `@icontract` and `@beartype` where applicable.

## 6. Documentation research and review (per openspec/config.yaml)

- [x] 6.1 Identify affected documentation: `docs/reference/debug-logging.md`, `docs/guides/troubleshooting.md`, `docs/adapters/azuredevops.md`; README.md (debug pointer); no new pages → no `docs/index.md` or `docs/_layouts/default.html` changes.
- [x] 6.2 Update debug-logging.md: extend "What Is Logged by Component" (ADO PATCH failure with response_body, patch_paths), add "Examining ADO API Errors" subsection (console + log, steps to analyze, link to custom mapping and troubleshooting).
- [x] 6.3 Update troubleshooting.md: add "Backlog refine or work item PATCH fails (400/422)" under Azure DevOps Issues (cause, read console, run with --debug, fix mapping, link to custom-field-mapping and debug-logging).
- [x] 6.4 Update adapters/azuredevops.md: add short "Error diagnostics" or troubleshooting note for PATCH failures linking to [Debug Logging](../reference/debug-logging.md#examining-ado-api-errors) and [Troubleshooting](../guides/troubleshooting.md#backlog-refine-or-work-item-patch-fails-400422).
- [x] 6.5 Verify README.md debug line still accurate (points to Debug Logging); add optional one-line note that with `--debug`, ADO API errors include response snippet and patch paths in the log.
- [x] 6.6 Confirm no new/moved pages → front-matter and `docs/_layouts/default.html` sidebar unchanged.

## 6b. Version bump, sync, and changelog (before PR)

- [x] 6b.1 Bump patch version (fix): 0.26.13 → 0.26.14.
- [x] 6b.2 Sync version in: `pyproject.toml`, `setup.py`, `src/__init__.py`, `src/specfact_cli/__init__.py`.
- [x] 6b.3 Add CHANGELOG.md entry: new section `## [0.26.14] - YYYY-MM-DD` with `### Fixed (0.26.14)` describing ADO error logging and user-facing UX improvements (fixes #162).

## 7. Create Pull Request to dev

- [ ] 7.1 Ensure all changes are committed: `git add .` and `git commit -m "fix: improve ADO backlog refine error logging and user-facing error UX (fixes nold-ai/specfact-cli#162)"`
- [ ] 7.2 Push to remote: `git push origin bugfix/improve-ado-backlog-refine-error-logging`
- [ ] 7.3 Create PR body with Fixes nold-ai/specfact-cli#162, summary from proposal, and OpenSpec change ID: `improve-ado-backlog-refine-error-logging`
- [ ] 7.4 Create PR: `gh pr create --repo nold-ai/specfact-cli --base dev --head bugfix/improve-ado-backlog-refine-error-logging --title "fix: improve ADO backlog refine error logging and user-facing error UX" --body-file <path>`
- [ ] 7.5 Verify PR and branch are linked to issue #162 (Development section).
