# Change: Improve Backlog Refine and CLI Startup

## Why

1. **Startup delay**: CLI can take 5–10s before first output (e.g. under xagt). Users need version line before any checks.
2. **Backlog refine --limit**: With `--limit N`, if the first N items are already refined, the user gets N skips every run. We need `--ignore-refined` (default) so limit applies to items that need refinement.
3. **Focused refinement**: No way to refine one story by ID. Add `--id ISSUE_ID`.
4. **Copilot loop**: Prompt should instruct AI to present story → ambiguities → clarify → re-refine until approved → update (interactive, stakeholder-friendly).

## What Changes

- **MODIFY** `src/specfact_cli/cli.py` – Ensure first output (version line) before startup checks; optional PyPI timeout.
- **MODIFY** `src/specfact_cli/commands/backlog_commands.py` – Add `--ignore-refined`/`--no-ignore-refined`, `--id`; filter logic so limit applies to items needing refinement when ignore-refined.
- **MODIFY** `src/specfact_cli/utils/startup_checks.py` – Optional timeout for `check_pypi_version()`.
- **MODIFY** `resources/prompts/specfact.backlog-refine.md` – Add interactive refinement (Copilot) section: present story → ambiguities → ask clarification → re-refine until approved → then update.
- **MODIFY** `openspec/specs/backlog-refinement/spec.md` – Add scenarios for ignore-refined and --id.
- **NEW** Tests for ignore-refined and --id behavior.
- **MODIFY** Docs/AGENTS.md – Document `--skip-checks` for startup.

## Capabilities

- **backlog-refinement**: Ignore already-refined by default; add --id for single-item refinement; prompt interactive loop (prompt-level).
- **cli-performance**: First output before startup checks; optional PyPI timeout (existing cli-performance spec).

## Impact

**Affected Specs**: backlog-refinement, cli-performance (reference only)

**Affected Code**:

- `cli.py`, `startup_checks.py`, `backlog_commands.py`, `specfact.backlog-refine.md`

**Integration Points**:

- Backlog adapters (unchanged; post-filter by id and needs-refinement).
- Copilot/Cursor prompt consumers (improved prompt text).

**Breaking Changes**: None. New options; default `--ignore-refined` changes which items count toward limit (behavioral improvement).

**Documentation**: AGENTS.md or docs for `--skip-checks`; backlog refine docs for `--ignore-refined`, `--no-ignore-refined`, `--id`.

## Source Tracking

- **GitHub Issue**: #166
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/166>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
