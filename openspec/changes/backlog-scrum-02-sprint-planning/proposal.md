# Change: Backlog Scrum — Sprint Planning and Capacity Commitment

## Why


SpecFact CLI supports sprint/release assignment and story points at the backlog-item level, but there is no first-class support for sprint capacity (available story points per sprint), commitment vs capacity comparison (over/under committed), or a CLI/export view that shows sprint-level summary. Teams must manually sum story points and compare to capacity outside SpecFact.

This change is part of the **`backlog-scrum` module** — the Scrum-framework module. Sprint planning is delivered as a capability of the same module as standup (backlog-scrum-01).

## Module Package Structure

```
modules/backlog-scrum/
  module-package.yaml          # updated: add 'backlog sprint-summary' to commands
  src/backlog_scrum/
    commands/
      sprint_summary.py        # specfact backlog sprint-summary
    planning/
      capacity.py              # sprint capacity config loading, commitment aggregation
```

**Config**: Sprint capacity stored in `.specfact/scrum.yaml` (all Scrum-specific config consolidated here).

## Module Package Structure

```
modules/backlog-scrum/
  module-package.yaml          # updated: add 'backlog sprint-summary' to commands
  src/backlog_scrum/
    commands/
      sprint_summary.py        # specfact backlog sprint-summary
    planning/
      capacity.py              # sprint capacity config loading, commitment aggregation
```

**Config**: Sprint capacity stored in `.specfact/scrum.yaml` (all Scrum-specific config consolidated here).

## What Changes


- **NEW**: Sprint capacity config via `.specfact/scrum.yaml` — capacity in story points per sprint identifier; loaded by `modules/backlog-scrum/src/backlog_scrum/planning/capacity.py`.
- **NEW**: When listing or exporting backlog items filtered by sprint, compute total story points and compare to capacity (if configured).
- **NEW**: CLI command `specfact backlog sprint-summary` in `modules/backlog-scrum/src/backlog_scrum/commands/sprint_summary.py`: sprint id, total committed points, capacity, difference (over/under). Declared in `module-package.yaml`; no changes to `cli.py`.
- **EXTEND** (plan E2): Optional `sprint_goal` support in `.specfact/scrum.yaml`; show alignment hints. Include risk rollup section from backlog-safe-02 when present. Add "DoR coverage" summary via policy-engine-01 when present.

## Capabilities
- **backlog-scrum** (sprint planning): Capacity config load from `.specfact/scrum.yaml`; commitment sum by sprint; over/under comparison; `backlog sprint-summary` CLI/export; optional sprint_goal and alignment hints; risk rollup and DoR coverage when backlog-safe-02 and policy-engine-01 are available.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #170
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/170>
- **Last Synced Status**: proposed
- **Sanitized**: false
