# Change: Improve Backlog Refine and CLI Startup

## Why

Four improvements are needed:

1. **Startup delay**: On machines with security scanning (e.g. xagt), the CLI takes 5–10s before first output. Global startup checks (template validation, PyPI version check) and backlog refine init block the first message. Users need faster feedback (e.g. version line before checks).

2. **Backlog refine --limit loop**: With `--limit N`, the first N items are processed; already-refined items are skipped in the loop. If the first N are all already refined, the user gets N skips every run—always the same stories. We need `--ignore-refined` (default) so limit applies to items that *need* refinement.

3. **Focused refinement**: There is no way to refine a single story by ID. Users need `--id ISSUE_ID` for focused refinement.

4. **Copilot interactive refinement**: The backlog-refine prompt does not instruct the AI to show each story, explain ambiguities, ask for clarification, re-refine until the user approves, then update. The experience should be interactive and stakeholder-friendly (MEB goal) at the prompt level.

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
