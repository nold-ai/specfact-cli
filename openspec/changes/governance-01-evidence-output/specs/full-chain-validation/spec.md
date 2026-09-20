## Scope rescope — 2026-09-20

Emit compact current-run observations and artifact references; historical chronology is separate and optional. Do not require a RED ledger, seal lineage, or the complete validation graph just to record lean CI results. Existing graph-output integration remains this issue's scope; <https://github.com/nold-ai/specfact-cli/issues/740> must not depend on its delivery.

This owner-requested scope amendment takes precedence over conflicting default-workflow or dependency wording below. It changes planning only; runtime policy is unchanged. [Replacement policy](../../../requirements-09-minimal-evidence/proposal.md).

## MODIFIED Requirements

### Requirement: Full Chain Validation

Full-chain validation SHALL emit governance-ready evidence artifacts.

#### Scenario: Evidence artifact is written with stable schema envelope

- **GIVEN** full-chain validation executes with evidence output enabled
- **WHEN** command completes
- **THEN** evidence includes schema version, timestamp, profile, policy mode, layer summaries, and overall status
- **AND** artifact path is printed for CI ingestion.
