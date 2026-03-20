# TDD Evidence: bugfix-02-ado-import-payload-slugging

## Failing First

- `2026-03-20`: `hatch run pytest tests/unit/adapters/test_ado.py tests/unit/adapters/test_github.py tests/integration/sync/test_ado_backlog_sync.py tests/integration/sync/test_backlog_sync.py tests/unit/sync/test_bridge_sync_import.py -q`
  failed with `5 failed, 73 passed` before the fix. The failures showed two regressions:
  selective ADO fetch reduced the work item to a summary payload without native
  `fields`, and shared backlog import fell back to numeric-only change IDs such
  as `123` instead of title-derived slugs.
- `2026-03-20`: audit of adjacent import paths confirmed that the shared
  `import_backlog_item_as_proposal()` helper is used by both the ADO and GitHub
  adapters, so the title-first normalization fix had to be applied in the
  shared backlog adapter rather than only in the ADO implementation.

## Passing

- `2026-03-20`: `hatch run pytest tests/unit/adapters/test_ado.py tests/unit/adapters/test_github.py tests/unit/sync/test_bridge_sync_import.py -q`
  passed with `76 passed`. This covers native selective fetch for ADO and
  GitHub, title-first imported change IDs, deterministic collision suffixes,
  and the bridge selective-import contract.

- `2026-03-20`: `openspec validate bugfix-02-ado-import-payload-slugging --strict`
  passed.
- `2026-03-20`: `hatch run format`
  passed after reformatting the touched files.
- `2026-03-20`: `hatch run type-check`
  passed with `0 errors`.
- `2026-03-20`: `hatch run yaml-lint`
  passed.
- `2026-03-20`: `hatch run contract-test`
  exited `0` using cached results (`No modified files detected - using cached results`).
- `2026-03-20`: `hatch run smart-test`
  exited `0`; the command skipped mapped test execution for this delta and emitted only its standard coverage warning.
- `2026-03-20`: `hatch run specfact code review run --json --out .codex-bugfix-02-review.json src/specfact_cli/adapters/ado.py src/specfact_cli/adapters/backlog_base.py src/specfact_cli/adapters/github.py tests/unit/adapters/test_ado.py tests/unit/adapters/test_github.py tests/unit/sync/test_bridge_sync_import.py tests/integration/sync/test_ado_backlog_sync.py tests/integration/sync/test_backlog_sync.py`
  exported the governed review report to `.codex-bugfix-02-review.json`. The overall report still fails because the touched legacy adapter files already carry a large historical baseline, but filtering the report to the lines changed by this fix yields `0` findings.

## Outstanding Gate Caveat

- `2026-03-20`: `hatch run lint`
  still exits non-zero in this worktree because the repository-wide lint script (`ruff format . --check && basedpyright ... && ruff check . && pylint src tests tools`) surfaces existing baseline findings outside this bugfix. The modified lines for this change were reviewed separately via `.codex-bugfix-02-review.json` and returned `0` changed-line findings.
