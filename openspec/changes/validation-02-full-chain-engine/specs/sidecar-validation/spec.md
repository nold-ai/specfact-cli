## Scope rescope — 2026-09-20

Consume current_execution independently from optional chronology. No global graph, full-chain completeness, or historical proof prerequisite for <https://github.com/nold-ai/specfact-cli/issues/740>. Missing mappings remain unassessed coverage, not fabricated completeness. Preserve graph validation for users who request that capability.

This owner-requested scope amendment takes precedence over conflicting default-workflow or dependency wording below. It changes planning only; runtime policy is unchanged. [Replacement policy](../../../requirements-09-minimal-evidence/proposal.md).

## MODIFIED Requirements

### Requirement: Sidecar Validation

The sidecar validation capability SHALL support full-chain payload checks in addition to spec-code checks.

#### Scenario: Sidecar consumes full-chain input set

- **GIVEN** requirement and architecture artifact paths are provided
- **WHEN** sidecar validation runs
- **THEN** sidecar validates layered chain references
- **AND** results are merged into full-chain evidence output.

#### Scenario: Existing spec-code validation remains supported

- **GIVEN** sidecar is invoked without requirements/architecture inputs
- **WHEN** validation executes
- **THEN** existing spec-code validation behavior continues unchanged.
