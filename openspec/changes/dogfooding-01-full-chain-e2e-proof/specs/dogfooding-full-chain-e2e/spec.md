## ADDED Requirements

### Requirement: End-to-End Dogfooding Proof
The system SHALL provide a reproducible dogfooding workflow that proves full-chain traceability from backlog to CI evidence.

#### Scenario: Full chain proof is generated for a real backlog slice
- **WHEN** dogfooding workflow runs for selected SpecFact backlog items
- **THEN** each item is traceable through requirement, architecture, spec, code/test, and evidence outputs
- **AND** missing links are reported as gate failures

### Requirement: Dogfooding Evidence Is CI-Consumable
The system SHALL produce machine-readable evidence artifacts for the dogfooding run.

#### Scenario: CI validates dogfooding proof
- **WHEN** CI executes the dogfooding full-chain run
- **THEN** evidence artifacts are emitted in a stable schema
- **AND** wave gate status is derivable from those artifacts

#### Scenario: Dogfood proof includes clean-code evidence
- **WHEN** the dogfooding proof runs with code-quality enabled
- **THEN** the resulting evidence bundle includes clean-code category results
- **AND** release-readiness proof fails if required clean-code categories regress
