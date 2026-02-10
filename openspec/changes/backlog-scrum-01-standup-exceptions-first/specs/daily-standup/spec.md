# Daily standup exceptions-first (E1 delta)

## ADDED Requirements

Delta on top of archived `daily-standup-progress-support`; extends `specfact backlog daily` with exceptions-first order and mode.

### Requirement: Exceptions-first section order

The system SHALL order `specfact backlog daily` output sections by default as: (1) blockers and dependency-critical items, (2) policy failures (DoR/DoD/flow when Policy Engine available), (3) aging items / stalled work (when data exists), (4) normal status.

**Rationale**: Plan E1—teams see risks first.

#### Scenario: Standup output shows exceptions first

**Given**: Policy Engine (unify-policies-engine) and/or aging/flow data are available

**When**: The user runs `specfact backlog daily` (no override)

**Then**: The output includes an "Exceptions" section by default (blockers, policy failures, aging/stalled when available) before normal status

**Acceptance Criteria**:

- `backlog daily` includes an "Exceptions" section by default when exception data exists.

### Requirement: Mode switch (scrum|kanban|safe)

The system SHALL support `--mode scrum|kanban|safe` to change defaults for filters and sections (e.g. Kanban: flow columns; SAFe: PI context).

**Rationale**: Plan E1—ceremony-native defaults per framework.

#### Scenario: Standup with mode

**Given**: SpecFact CLI and backlog adapter

**When**: The user runs `specfact backlog daily --mode kanban`

**Then**: Default filters and section behavior align with Kanban (e.g. flow-focused); when `--mode safe`, PI context when available

**Acceptance Criteria**:

- `--mode scrum|kanban|safe` changes defaults; existing backlog daily behavior otherwise unchanged.

### Requirement: Patch integration for standup notes

The system SHALL integrate with patch mode (patch-mode-preview-apply) to propose standup notes or missing fields as patch when `--patch` is used.

**Rationale**: Plan E1—actionable standup output.

#### Scenario: Standup with patch proposal

**Given**: Patch mode is available

**When**: The user runs `specfact backlog daily --patch`

**Then**: The command may emit a patch proposal (standup notes or missing fields) for user review/apply

**Acceptance Criteria**:

- When patch mode is available and `--patch` is set, standup can propose patch; no silent writes.
