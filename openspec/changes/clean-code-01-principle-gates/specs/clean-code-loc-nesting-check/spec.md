## ADDED Requirements

### Requirement: Staged LOC, Nesting, and Parameter Checks
The repository SHALL adopt the expanded KISS metrics through a staged rollout that starts with the Phase A thresholds from the 2026-03-22 plan.

#### Scenario: Phase A thresholds are enforced first
- **GIVEN** the clean-code review checks are enabled for specfact-cli
- **WHEN** LOC-per-function findings are evaluated
- **THEN** warning and error thresholds start at `>80` and `>120`
- **AND** nesting-depth and parameter-count checks are active in the same review run

#### Scenario: Phase B remains deferred until cleanup is complete
- **GIVEN** stricter LOC thresholds of `>40` and `>80` are planned
- **WHEN** this change is implemented
- **THEN** Phase B remains documented as a future tightening step
- **AND** the current change does not silently promote Phase B to a hard gate
