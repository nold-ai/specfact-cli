# Change: Kanban Flow Metrics + WIP/Aging Signals — Δ4

## Why

Kanban teams won't use sprint-based commands. Today SpecFact has Policy Engine (#176) and dependency graph (#116), but no Kanban-native workflow: WIP limits, aging WIP, flow metrics (cycle time/throughput), blocked time. Without `backlog flow` and `.specfact/kanban.yaml`, Kanban teams see SpecFact as "Scrum-only."

## What Changes

- **NEW**: Add CLI command `specfact backlog flow` (or `backlog flow-metrics`) for Kanban flow view: WIP per column, aging WIP, cycle time/throughput (when data exists), blocked time.
- **NEW**: Config `.specfact/kanban.yaml` for WIP limits, column definitions, aging thresholds; integrate with Policy Engine (#176) for entry/exit policies.
- **NEW**: Output flow metrics (WIP, aging, cycle time, throughput) in machine-readable (JSON) and human-readable (Markdown) formats.
- **EXTEND**: Policy Engine (#176) supports Kanban entry/exit policies per column when kanban config is present.
- **EXTEND**: When `backlog daily` is run with `--mode kanban` and flow data exists, output MAY include a "flow exceptions" section (WIP/aging violations); integration with daily-standup and ceremony-cockpit when Kanban flow change is present.
- **EXTEND**: Documentation (agile-scrum-workflows) for Kanban flow and WIP/aging.

## Capabilities

- **kanban-flow**: `backlog flow` command; `.specfact/kanban.yaml` (WIP limits, columns, aging); flow metrics (WIP, aging, cycle time, throughput, blocked); Policy Engine integration for Kanban policies.

## Impact

- **Affected specs**: New `openspec/changes/backlog-06-kanban-flow-metrics/specs/kanban-flow/spec.md` (Given/When/Then for flow command, config, metrics, policy integration).
- **Affected code**: New command `specfact backlog flow`; kanban config loader; flow metrics aggregation; integration with Policy Engine for Kanban entry/exit.
- **Affected documentation** (<https://docs.specfact.io>): docs/guides/agile-scrum-workflows.md.
- **Integration points**: unify-policies-engine (#176), add-backlog-dependency-analysis-and-commands (#116) for backlog data.
- **Backward compatibility**: Additive; new command and config; existing Scrum commands unchanged.

## Source Tracking

- **GitHub Issue**: #183
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/183>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
