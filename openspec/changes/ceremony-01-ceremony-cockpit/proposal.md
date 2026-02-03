# Change: Ceremony Cockpit (UX layer for findability) — Δ3

## Why

Teams think in ceremonies ("standup," "refinement," "planning"). Without ceremony entry points, adoption friction remains high—users must remember `backlog daily`, `backlog refine`, `backlog sprint-summary` instead of `ceremony standup`, `ceremony refinement`, `ceremony planning`. Ceremony aliases plus mode switch (scrum|kanban|safe) and exceptions-first defaults are a pure UX/ergonomics win with minimal implementation cost.

## What Changes

- **NEW**: Add ceremony-oriented entry points: `specfact ceremony standup` → `backlog daily`, `specfact ceremony refinement` → `backlog refine`, `specfact ceremony planning` → `backlog sprint-summary` (and optional `ceremony flow`, `ceremony pi-summary` when those changes exist).
- **NEW**: Each ceremony command SHALL emit human view (Markdown/table), machine view (JSON when underlying backlog command supports `--output json`), and optional copilot prompt export; ceremony layer inherits or forwards these output formats from the underlying backlog command.
- **NEW**: Add `--mode scrum|kanban|safe` at ceremony level so defaults for filters and sections follow framework.
- **EXTEND**: Exceptions-first default section order (blockers, policy failures, aging, normal) when applicable; integrate with daily-standup-exceptions-first (E1) and Policy Engine (#176).
- **EXTEND**: Documentation (agile-scrum-workflows) for ceremony commands and mode switch.

## Capabilities

- **ceremony-cockpit**: Ceremony aliases (standup, refinement, planning, optional flow/pi-summary); mode switch (scrum|kanban|safe); exceptions-first defaults; Policy Engine integration for section ordering.

## Impact

- **Affected specs**: New `openspec/changes/ceremony-01-ceremony-cockpit/specs/ceremony-cockpit/spec.md` (Given/When/Then for ceremony aliases, mode, output order).
- **Affected code**: New command group `specfact ceremony` with subcommands delegating to backlog; `--mode` and default section order wiring.
- **Affected documentation** (<https://docs.specfact.io>): docs/guides/agile-scrum-workflows.md.
- **Integration points**: daily-standup-exceptions-first (E1), sprint-planning-capacity-commitment-support (#170), unify-policies-engine (#176); optional kanban-flow-metrics (Δ4), safe-pi-planning (Δ5).
- **Backward compatibility**: Additive; existing `backlog daily`, `backlog refine`, `backlog sprint-summary` unchanged; ceremony is an alias layer.

## Source Tracking

- **GitHub Issue**: #185
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/185>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
