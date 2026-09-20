## Scope rescope — 2026-09-20

Measure bounded defect-detection and operational overhead on real changes. Use existing CI artifacts; retain failures/reproductions that demonstrate test sensitivity. No mandatory immutable RED history or repeated seal approvals for the lean dogfood path. Stronger assurance experiments remain explicitly selected.

This owner-requested scope amendment takes precedence over conflicting default-workflow or dependency wording below. It changes planning only; runtime policy is unchanged. [Replacement policy](../../../requirements-09-minimal-evidence/proposal.md).

## ADDED Requirements

### Requirement: End-to-End Dogfooding Proof

The ordinary dogfooding workflow SHALL evaluate a bounded real change using
existing current-run CI outputs, relevant defect reproductions, remediation and
rerun comparison, with concise observations of operational overhead. It SHALL
NOT require full-chain traceability or retained RED chronology. An explicitly
selected full-chain experiment SHALL still validate all links it claims.

#### Scenario: Ordinary dogfood uses existing validation results

- **GIVEN** a real change with current validation results and ordinary MEB policy
- **WHEN** the dogfood run evaluates defects, remediation and the resulting rerun
- **THEN** it references existing CI artifacts and summarizes observed improvement and overhead
- **AND** absent full-chain links or historical RED records are not gate failures.

#### Scenario: Full chain proof is generated for a real backlog slice

- **GIVEN** a full-chain assurance experiment is explicitly selected
- **WHEN** that workflow runs for selected SpecFact backlog items
- **THEN** each item is traceable through requirement, architecture, spec, code/test, and evidence outputs
- **AND** missing links are reported as gate failures

### Requirement: Dogfooding Evidence Is CI-Consumable

The system SHALL reuse existing machine-readable validation outputs and CI artifact references for ordinary dogfood. Additional link evidence SHALL be required only for an explicitly selected full-chain experiment.

#### Scenario: CI validates dogfooding proof

- **GIVEN** a full-chain assurance experiment is explicitly selected
- **WHEN** CI executes that dogfooding run
- **THEN** evidence artifacts are emitted in a stable schema
- **AND** wave gate status is derivable from those artifacts

#### Scenario: Dogfood proof includes clean-code evidence

- **WHEN** the dogfooding proof runs with code-quality enabled
- **THEN** the resulting evidence bundle includes clean-code category results
- **AND** release-readiness proof fails if required clean-code categories regress
