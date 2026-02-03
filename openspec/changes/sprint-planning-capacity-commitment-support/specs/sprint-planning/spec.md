# Sprint planning (capacity and commitment)

## ADDED Requirements

### Requirement: Sprint capacity configuration

The system SHALL support loading sprint capacity configuration from project config (e.g. `.specfact/sprint_capacity.yaml`) mapping sprint identifiers to available story points per sprint.

**Rationale**: Teams need to define capacity (e.g. velocity or available points) per sprint to compare with commitment.

#### Scenario: Load sprint capacity config from project

**Given**: A project with a sprint capacity config file (e.g. `.specfact/sprint_capacity.yaml`) defining capacity per sprint (e.g. sprint_1: 40, sprint_2: 38)

**When**: The user runs a backlog command that uses sprint summary (e.g. `specfact backlog sprint-summary` or equivalent)

**Then**: The system loads the capacity config and uses it for comparison

**And**: If no capacity config exists, the system shows committed points only or a clear message that capacity is not configured

**Acceptance Criteria**:

- Capacity config schema is documented; loader does not crash on missing or invalid config (report clearly).

### Requirement: Commitment sum by sprint

The system SHALL compute total committed story points per sprint from backlog items assigned to that sprint (BacklogItem.sprint + story_points).

**Rationale**: Commitment is derived from items in the sprint; no manual sum required.

#### Scenario: Sum committed points for a sprint

**Given**: Backlog items with sprint assignment and story_points (e.g. items A, B, C in sprint_1 with points 13, 8, 5)

**When**: The user requests sprint summary for that sprint (e.g. `specfact backlog sprint-summary --sprint sprint_1`)

**Then**: The system sums story_points for all items in that sprint and reports total committed points (e.g. 26)

**Acceptance Criteria**:

- Sum is deterministic; items without story_points are treated as 0 or excluded per documented behavior.

### Requirement: Over/under commitment output

The system SHALL compare total committed points to capacity (when configured) and report over-commitment (committed > capacity) or under-commitment/slack (committed < capacity).

**Rationale**: Teams need to see at a glance whether the sprint is over or under committed.

#### Scenario: Sprint summary with capacity comparison

**Given**: Capacity for sprint_1 is 40 points and committed points from backlog items are 26

**When**: The user runs `specfact backlog sprint-summary` for that sprint

**Then**: The output shows sprint id, total committed points, capacity, and difference (e.g. sprint_1, committed: 26, capacity: 40, gap: -14 or "under by 14")

**Acceptance Criteria**:

- Output is readable (CLI and/or export); when capacity is not configured, show committed only; over-commitment shows positive gap or "over by X".

### Requirement: Sprint summary under backlog group

The system SHALL expose sprint summary under the backlog command group (e.g. `specfact backlog sprint-summary`); there SHALL be no top-level `specfact sprint` command.

**Rationale**: Align with other scrum/backlog features under `specfact backlog`.

#### Scenario: Invoke sprint summary via backlog

**Given**: SpecFact CLI is installed and project has backlog and optional capacity config

**When**: The user runs `specfact backlog sprint-summary` (with optional `--sprint <id>`)

**Then**: The command runs and outputs sprint-level summary (committed, capacity if configured, gap)

**Acceptance Criteria**:

- Command is discoverable under `specfact backlog --help`; behavior matches spec scenarios above.

### Requirement: Sprint summary with risk and DoR (E2 extension)

The system SHALL include in sprint summary output (when dependencies are available): risk rollup (top blockers, risk level), and DoR coverage (pass rate for sprint scope) via Policy Engine. Optional sprint_goal in config SHALL be shown as alignment hint when present.

**Rationale**: Plan E2—teams need capacity, committed, risk, top blockers, and DoR pass rate in one view.

#### Scenario: Sprint summary includes risk and DoR

**Given**: Policy Engine (unify-policies-engine) and risk rollups (explainable-risk-rollups) are available; sprint has items with DoR state

**When**: The user runs `specfact backlog sprint-summary` for that sprint

**Then**: The output includes capacity, committed, and when available: risk level, top blockers, DoR pass rate; if sprint_goal is in config, show alignment hint

**Acceptance Criteria**:

- Sprint summary includes: capacity, committed, risk (when available), top blockers (when available), DoR pass rate (when Policy Engine available). Optional sprint_goal and alignment hints.
