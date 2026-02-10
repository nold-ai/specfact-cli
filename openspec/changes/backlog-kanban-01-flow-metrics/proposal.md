# Change: Backlog Kanban — Flow Metrics and WIP/Aging Signals

## Why


Kanban teams won't use sprint-based commands. Today SpecFact has policy-engine-01 and backlog-core-01, but no Kanban-native workflow: WIP limits, aging WIP, flow metrics (cycle time/throughput), blocked time. Without a dedicated `backlog-kanban` module providing `backlog flow` and `.specfact/kanban.yaml`, Kanban teams see SpecFact as "Scrum-only."

This change establishes the **`backlog-kanban` module** — the Kanban-framework module that provides WIP/aging/flow metrics and Kanban-specific policy hooks.

## Module Package Structure

```
modules/backlog-kanban/
  module-package.yaml          # name: backlog-kanban; commands: backlog flow
  src/backlog_kanban/
    __init__.py
    main.py                    # typer.Typer app — backlog flow command group
    commands/
      flow.py                  # specfact backlog flow
    metrics/
      wip.py                   # WIP per column, aging WIP
      cycle_time.py            # cycle time, throughput (when data exists)
      blocked.py               # blocked time tracking
    config/
      kanban_config.py         # .specfact/kanban.yaml loader
    integrations/
      policy_hook.py           # Kanban entry/exit policies (policy-engine-01)
      standup_hook.py          # 'flow exceptions' section for backlog daily --mode kanban
```

**`module-package.yaml` declares:**
- `name: backlog-kanban`
- `version: 0.1.0`
- `commands: [backlog flow]`
- `dependencies: [backlog-core]`
- `optional_dependencies: [policy-engine]`
- `publisher:` + `integrity:` — arch-06 marketplace readiness

**Config**: `.specfact/kanban.yaml` — WIP limits, column definitions, aging thresholds. Separate from `.specfact/scrum.yaml` (backlog-scrum module).

## Module Package Structure

```
modules/backlog-kanban/
  module-package.yaml          # name: backlog-kanban; commands: backlog flow
  src/backlog_kanban/
    __init__.py
    main.py                    # typer.Typer app — backlog flow command group
    commands/
      flow.py                  # specfact backlog flow
    metrics/
      wip.py                   # WIP per column, aging WIP
      cycle_time.py            # cycle time, throughput (when data exists)
      blocked.py               # blocked time tracking
    config/
      kanban_config.py         # .specfact/kanban.yaml loader
    integrations/
      policy_hook.py           # Kanban entry/exit policies (policy-engine-01)
      standup_hook.py          # 'flow exceptions' section for backlog daily --mode kanban
```

**`module-package.yaml` declares:**
- `name: backlog-kanban`
- `version: 0.1.0`
- `commands: [backlog flow]`
- `dependencies: [backlog-core]`
- `optional_dependencies: [policy-engine]`
- `publisher:` + `integrity:` — arch-06 marketplace readiness

**Config**: `.specfact/kanban.yaml` — WIP limits, column definitions, aging thresholds. Separate from `.specfact/scrum.yaml` (backlog-scrum module).

## What Changes


- **NEW**: CLI command `specfact backlog flow` in `modules/backlog-kanban/src/backlog_kanban/commands/flow.py`: WIP per column, aging WIP, cycle time/throughput (when data exists), blocked time. Declared in `module-package.yaml`; no changes to `cli.py`.
- **NEW**: Config `.specfact/kanban.yaml` for WIP limits, column definitions, aging thresholds; loaded by `modules/backlog-kanban/src/backlog_kanban/config/kanban_config.py`.
- **NEW**: Output flow metrics in machine-readable (JSON) and human-readable (Markdown) formats.
- **EXTEND** (policy-engine-01): When policy-engine-01 is present, register Kanban entry/exit policies per column; policies evaluated when kanban config exists. Graceful no-op if policy-engine-01 not installed.
- **EXTEND** (backlog-scrum-01): When `backlog daily` is run with `--mode kanban` and flow data exists, output MAY include a "flow exceptions" section (WIP/aging violations) injected by this module's standup hook.
- **EXTEND** (arch-07 schema extensions): Register `backlog_kanban.flow_state` extension on `BacklogItem` via `module-package.yaml` — stores column position, time-in-column, WIP contribution for Kanban items.

## Capabilities
- **backlog-kanban**: `backlog flow` command; `.specfact/kanban.yaml` (WIP limits, columns, aging); flow metrics (WIP, aging, cycle time, throughput, blocked); policy-engine-01 integration for Kanban entry/exit policies; `--mode kanban` standup flow exceptions section.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #183
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/183>
- **Last Synced Status**: proposed
- **Sanitized**: false
