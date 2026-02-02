# Change: Daily standup exceptions-first and flow/policy hooks (E1 delta)

## Why

The archived change `daily-standup-progress-support` (#168) delivers standup view, interactive review, and Copilot export. Teams love tools that surface blockers and risks first. This delta extends standup with exceptions-first default section order, optional `--mode scrum|kanban|safe`, and integration with Policy Engine and patch mode so standup output highlights policy failures and aging/stalled work before normal status.

## What Changes

- **EXTEND** (plan E1): Default section order for `specfact backlog daily`: (1) blockers and dependency-critical items, (2) policy failures (DoR/DoD/flow), (3) aging items / stalled work (when data exists), (4) normal status.
- **NEW**: Add `--mode scrum|kanban|safe` to change defaults for filters and sections.
- **EXTEND**: Integrate `--patch` (patch-mode-preview-apply) to propose standup notes or missing fields as patch.
- **EXTEND**: Documentation (agile-scrum-workflows, devops-adapter-integration) for exceptions-first standup and mode switch.

## Capabilities

- **daily-standup-exceptions**: Exceptions-first section order (blockers, policy failures, aging, normal); `--mode scrum|kanban|safe`; optional patch integration for standup notes.

## Impact

- **Affected specs**: New `openspec/changes/daily-standup-exceptions-first/specs/daily-standup/spec.md` (delta on daily-standup; Given/When/Then for exceptions-first order, mode, patch).
- **Affected code**: `src/specfact_cli/commands/backlog_commands.py` (daily command: section order, --mode, patch hook); depends on unify-policies-engine and patch-mode-preview-apply when available.
- **Affected documentation** (<https://docs.specfact.io>): docs/guides/agile-scrum-workflows.md, docs/guides/devops-adapter-integration.md.
- **Integration points**: Archived daily-standup-progress-support; unify-policies-engine (Δ1); patch-mode-preview-apply (Δ2).
- **Backward compatibility**: Additive; default section order becomes exceptions-first when policy/flow data exists; existing standup UX unchanged otherwise.

## Source Tracking

- **GitHub Issue**: #175
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/175>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
