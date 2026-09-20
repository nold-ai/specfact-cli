## Scope rescope — 2026-09-20

Emit compact current-run observations and artifact references; historical chronology is separate and optional. Do not require a RED ledger, seal lineage, or the complete validation graph just to record lean CI results. Existing graph-output integration remains this issue's scope; <https://github.com/nold-ai/specfact-cli/issues/740> must not depend on its delivery.

This owner-requested scope amendment takes precedence over conflicting default-workflow or dependency wording below. It changes planning only; runtime policy is unchanged. [Replacement policy](../../../requirements-09-minimal-evidence/proposal.md).

## ADDED Requirements

### Requirement: Governance Evidence Output

The system SHALL produce machine-readable governance evidence suitable for CI and audit ingestion.

#### Scenario: CI-consumable evidence includes policy and exception context

- **GIVEN** validation runs in CI mode
- **WHEN** evidence is generated
- **THEN** policy results and active exception references are included
- **AND** each exception includes identifier and expiration metadata.

#### Scenario: Evidence contains layer-level coverage metrics

- **GIVEN** full-chain validation has transition results
- **WHEN** governance evidence is emitted
- **THEN** each layer contains pass/fail/advisory counts and coverage percentages
- **AND** overall verdict is derivable from the evidence alone.

#### Scenario: Evidence carries clean-code results as a parallel quality dimension

- **GIVEN** a validation run includes `specfact review` clean-code output
- **WHEN** governance evidence is emitted
- **THEN** the envelope includes a top-level `code_quality` section with category counts and verdict
- **AND** clean-code data does not redefine or replace the traceability `validation_results.layers` structure
