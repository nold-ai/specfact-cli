# Risk Rollups (Explainable, Traceable)

## ADDED Requirements

### Requirement: Risk model with configurable inputs

The system SHALL provide a Risk model that aggregates inputs: dependency criticality, policy failures (DoR/DoD/flow), complexity flags, capacity overage, aging/WIP violations. Inputs SHALL be configurable so teams can enable/disable sources.

**Rationale**: Δ6—single substrate for "what might blow up" across ceremonies.

#### Scenario: Compute risk rollup

**Given**: A project with dependency graph and policy results (and optional capacity/complexity data)

**When**: The system computes risk rollup

**Then**: The system aggregates enabled inputs and produces a single score (low/medium/high)

**And**: Output includes traceable contributions: each input with reason and evidence pointer

**Acceptance Criteria**:

- Rollup score is low/medium/high; JSON output includes `contributions` array with source, reason, evidence pointer, and optional weight (contribution weight for explainability).

### Requirement: Risk rollup JSON output

The system SHALL produce machine-readable risk output: JSON with rollup score, contributions (source, reason, evidence pointer), and optional human-readable summary.

**Rationale**: Δ6—CI gates and tooling can consume risk without parsing prose.

#### Scenario: Export risk as JSON

**Given**: Risk rollup has been computed

**When**: The user requests JSON output (e.g. `--output json` or risk subcommand)

**Then**: The system outputs JSON with score, contributions array, and optional summary field

**Acceptance Criteria**:

- JSON schema includes score (enum: low/medium/high), contributions (array of { source, reason, evidence, optional weight }).

### Requirement: Risk integration in backlog commands

The system SHALL allow standup, refinement, and sprint-summary commands to include an optional risk section (rollup + top contributions) when risk data is available.

**Rationale**: Δ6—every ceremony can be exceptions-first.

#### Scenario: Standup shows risk section

**Given**: `specfact backlog daily` is run and dependency/policy (and optional capacity) data exists

**When**: Risk rollup is enabled (default or flag)

**Then**: Output includes a risk section with rollup score and top contributions (or "No significant risk" when low)

**Acceptance Criteria**:

- Risk section is present when enabled; does not block command when risk module or dependencies are unavailable.

### Requirement: Risk integration in verify-readiness (release)

When `backlog verify-readiness` (or equivalent release-readiness command) exists, the system SHALL allow it to include an optional risk section (rollup + top contributions) so release view includes risk.

**Rationale**: Δ6—risk used in verify-readiness (release) per 2026-02-01.

#### Scenario: Verify-readiness shows risk section

**Given**: `specfact backlog verify-readiness` (or equivalent) is run and risk data is available

**When**: Risk rollup is enabled (default or flag)

**Then**: Output MAY include a risk section with rollup score and top contributions when the command is implemented

**Acceptance Criteria**:

- When verify-readiness command exists, risk section is integrable; does not block when risk module is absent.
