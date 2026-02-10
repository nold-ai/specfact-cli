# Kanban Flow Metrics (WIP, Aging, Flow)

## ADDED Requirements

### Requirement: backlog flow command

The system SHALL provide `specfact backlog flow` (or `backlog flow-metrics`) that outputs Kanban flow view: WIP per column, aging WIP, cycle time/throughput when data exists, blocked time.

**Rationale**: Δ4—Kanban-native workflow.

#### Scenario: Run backlog flow

**Given**: A project with backlog adapter and optional `.specfact/kanban.yaml`

**When**: The user runs `specfact backlog flow`

**Then**: The system outputs WIP per column, aging items, and (when available) cycle time/throughput and blocked time

**And**: Output is available in JSON and Markdown

**Acceptance Criteria**:

- Command runs without error; output includes WIP and aging; cycle time/throughput when backlog supports it.
- When adapter does not provide state transitions (e.g. timestamps for column moves), the command runs in partial mode and output includes a clear disclaimer (e.g. "cycle time/throughput unavailable—partial mode").

### Requirement: Kanban config

The system SHALL support `.specfact/kanban.yaml` for WIP limits, column definitions, and aging thresholds. Config SHALL integrate with Policy Engine (#176) for Kanban entry/exit policies per column.

**Rationale**: Δ4—config-driven Kanban behavior.

#### Scenario: Load kanban config

**Given**: `.specfact/kanban.yaml` exists with columns and WIP limits

**When**: The user runs `specfact backlog flow` or Policy Engine validates Kanban policies

**Then**: The system loads kanban config and applies WIP/aging rules; missing config is handled gracefully

**Acceptance Criteria**:

- Config is optional; loader does not crash on missing/invalid config; Policy Engine can use columns for entry/exit.

### Requirement: Flow metrics output

The system SHALL produce flow metrics (WIP, aging, cycle time, throughput, blocked) in machine-readable (JSON) and human-readable (Markdown) formats.

**Rationale**: Δ4—CI and tooling can consume flow data.

#### Scenario: Export flow as JSON

**Given**: `specfact backlog flow` has run

**When**: The user requests JSON output (e.g. `--output json`)

**Then**: The system outputs JSON with WIP per column, aging count, and optional cycle time/throughput/blocked

**Acceptance Criteria**:

- JSON schema includes WIP, aging, and optional flow metrics; Markdown summary is human-readable.

### Requirement: Flow exceptions in backlog daily when Kanban mode

The system SHALL allow `specfact backlog daily` to include an optional "flow exceptions" section (WIP/aging violations) when run with `--mode kanban` and flow data exists (e.g. when kanban-flow-metrics change is present).

**Rationale**: Δ4 acceptance—backlog daily can include flow exceptions section when in Kanban mode.

#### Scenario: Standup with flow exceptions in Kanban mode

**Given**: User runs `specfact backlog daily --mode kanban` and flow data (WIP/aging) is available

**When**: Flow exceptions section is enabled (default or flag)

**Then**: Output MAY include a "flow exceptions" section with WIP limit violations and aging items when data exists

**Acceptance Criteria**:

- Flow exceptions section is optional; does not block daily when flow module or Kanban config is absent.
