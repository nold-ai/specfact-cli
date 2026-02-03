# Change: Sprint planning (capacity and commitment) support

## Why

SpecFact CLI supports sprint/release assignment and story points at the backlog-item level (e.g. BacklogItem fields, DoR), but there is no first-class support for sprint capacity (e.g. available story points per sprint), commitment vs capacity comparison (over/under committed), or a CLI/export view that shows sprint-level summary. Teams must manually sum story points and compare to capacity outside SpecFact.

## What Changes

- **NEW**: Introduce a lightweight notion of "sprint capacity" (e.g. config or optional file per project: capacity in story points per sprint identifier).
- **NEW**: When exporting or listing backlog items filtered by sprint, compute total story points for that sprint and compare to capacity (if configured).
- **NEW**: Add optional output (CLI and/or export) that shows: sprint id, total committed points, capacity, difference (over/under). Expose under the **backlog command group** as `specfact backlog sprint-summary` (or similar subcommand); do not add a top-level `specfact sprint` command.
- **EXTEND**: Documentation (agile-scrum-workflows, backlog-refinement) for sprint planning support.
- **EXTEND** (plan E2): Optional `sprint_goal` support in config; show alignment hints. Include risk rollup (explainable-risk-rollups) in sprint summary output. Add "DoR coverage" summary for sprint scope via Policy Engine (unify-policies-engine). **Acceptance**: Sprint summary includes: capacity, committed, risk, top blockers, DoR pass rate.

## Capabilities

- **sprint-planning**: Capacity config load, commitment sum by sprint, over/under commitment comparison, sprint-summary CLI/export output; optional sprint_goal and alignment hints; risk rollup and DoR coverage when Policy Engine and risk rollups are available.

## Impact

- **Affected specs**: New `openspec/changes/sprint-planning-capacity-commitment-support/specs/sprint-planning/spec.md` (Given/When/Then for capacity config, commitment sum, over/under output).
- **Affected code**: `src/specfact_cli/commands/backlog_commands.py` (sprint-summary subcommand or extend existing); `src/specfact_cli/` (models or config for sprint capacity, commitment aggregation).
- **Affected documentation** (<https://docs.specfact.io>): docs/guides/agile-scrum-workflows.md, docs/guides/backlog-refinement.md for sprint planning.
- **Integration points**: Existing backlog list/export; BacklogItem.sprint + story_points; adapter-agnostic (capacity from `.specfact/sprint_capacity.yaml` or similar).
- **Backward compatibility**: Additive only; existing backlog behavior unchanged unless user uses sprint-summary or config.

## Source Tracking

- **GitHub Issue**: #170
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/170>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
