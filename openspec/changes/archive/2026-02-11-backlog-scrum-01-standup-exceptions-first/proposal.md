# Change: Backlog Scrum — Daily Standup Exceptions-First

**GitHub issue**: [#175](https://github.com/nold-ai/specfact-cli/issues/175) — E1 delta; PRs must reference `Fixes nold-ai/specfact-cli#175`.

## Why

The archived change `daily-standup-progress-support` (#168) delivers standup view, interactive review, and Copilot export. Teams love tools that surface blockers and risks first. This delta extends standup with exceptions-first default section order, optional `--mode scrum|kanban|safe`, and integration with Policy Engine (policy-engine-01) and patch mode (patch-mode-01) so standup output highlights policy failures and aging/stalled work before normal status.

This change is part of the **`backlog-scrum` module** — the Scrum-framework module providing sprint planning, standup enhancement, story refinement, and DoD capabilities.

## Module Package Structure

```
modules/backlog-scrum/
  module-package.yaml          # name: backlog-scrum; commands extend 'backlog daily'
  src/backlog_scrum/
    __init__.py
    main.py                    # typer.Typer app — backlog command group extensions
    commands/
      daily.py                 # specfact backlog daily (exceptions-first, --mode scrum)
    sections/
      exceptions.py            # blockers, policy failures, aging detection
    integrations/
      policy_hook.py           # optional Policy Engine integration (policy-engine-01)
      patch_hook.py            # optional patch mode integration (patch-mode-01)
```

**`module-package.yaml` declares:**

- `name: backlog-scrum`
- `version: 0.1.0`
- `commands: [backlog daily (enhanced), backlog sprint-summary, ...]`
- `dependencies: [backlog-core]`
- `optional_dependencies: [policy-engine, patch-mode]`
- `publisher:` + `integrity:` — arch-06 marketplace readiness

**Important**: `backlog-scrum` extends the `backlog daily` command from the archived daily-standup module. The registry merges command extensions; the scrum module declares it enhances `backlog daily` with scrum-specific section ordering.

## Module Package Structure

```
modules/backlog-scrum/
  module-package.yaml          # name: backlog-scrum; commands extend 'backlog daily'
  src/backlog_scrum/
    __init__.py
    main.py                    # typer.Typer app — backlog command group extensions
    commands/
      daily.py                 # specfact backlog daily (exceptions-first, --mode scrum)
    sections/
      exceptions.py            # blockers, policy failures, aging detection
    integrations/
      policy_hook.py           # optional Policy Engine integration (policy-engine-01)
      patch_hook.py            # optional patch mode integration (patch-mode-01)
```

**`module-package.yaml` declares:**

- `name: backlog-scrum`
- `version: 0.1.0`
- `commands: [backlog daily (enhanced), backlog sprint-summary, ...]`
- `dependencies: [backlog-core]`
- `optional_dependencies: [policy-engine, patch-mode]`
- `publisher:` + `integrity:` — arch-06 marketplace readiness

**Important**: `backlog-scrum` extends the `backlog daily` command from the archived daily-standup module. The registry merges command extensions; the scrum module declares it enhances `backlog daily` with scrum-specific section ordering.

## What Changes

- **EXTEND** (plan E1): Default section order for `specfact backlog daily` when `backlog-scrum` module is loaded: (1) blockers and dependency-critical items, (2) policy failures (DoR/DoD/flow — from policy-engine-01 when present), (3) aging items / stalled work (when data exists), (4) normal status.
- **NEW**: Add `--mode scrum|kanban|safe` flag to `specfact backlog daily`; `scrum` is the default when this module is loaded.
- **EXTEND** (policy-engine-01): When policy-engine-01 is present, query policy results for each item and surface failures in section (2); graceful no-op if not installed.
- **EXTEND** (patch-mode-01): Integrate `--patch` flag to propose standup notes or missing fields as a patch file; graceful no-op if patch-mode-01 not installed.
- **EXTEND** (ADO comment context): Fetch ADO work item comments using the dedicated comments API resource (`workItems/{id}/comments`, API `7.1-preview.4`) with pagination so `backlog daily` and `backlog refine` can use complete comment history.
- **NEW**: Add optional comment windowing controls `--first-comments N` and `--last-comments N` for daily exports/summaries and refine preview output; refine export always keeps full comments (no truncation).
- **EXTEND**: Include comment context in refine write-mode prompts (full by default; first/last windowing optional for noise control).
- **EXTEND**: Add a Copilot instruction header to refine export files; refined import artifacts must omit the header and keep only item blocks.
- **EXTEND**: Make refine export guidance parity with interactive prompts by embedding equivalent refinement rules and per-item template guidance.
- **NEW**: Add optional issue windowing controls `--first-issues N` and `--last-issues N` for refine runs to process deterministic first/last item slices.
- **EXTEND** (interactive output UX): In `specfact backlog daily --interactive`, show only the latest comment plus a count hint for remaining comments and guidance to use export-to-file options for full comment context.
- **EXTEND** (prompt/docs): Update slash prompt templates and user docs so comment context behavior and comment-windowing options are explicit for everyday team workflows.

## Capabilities

- **backlog-scrum** (standup): Exceptions-first section order (blockers, policy failures, aging, normal); `--mode scrum|kanban|safe`; optional patch integration for standup notes; Policy Engine integration for policy failure surfacing.
- **backlog-scrum** (comment context): Full ADO comment retrieval for daily/refine, optional first/last comment limits, interactive last-comment-only rendering with export guidance, and aligned slash prompts/docs.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #220
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/220>
- **Last Synced Status**: proposed
- **Sanitized**: false
