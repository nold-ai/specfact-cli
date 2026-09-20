## Scope rescope — 2026-09-20

Emit compact current-run observations and artifact references; historical chronology is separate and optional. Do not require a RED ledger, seal lineage, or the complete validation graph just to record lean CI results. Existing graph-output integration remains this issue's scope; <https://github.com/nold-ai/specfact-cli/issues/740> must not depend on its delivery.

This owner-requested scope amendment takes precedence over conflicting default-workflow or dependency wording below. It changes planning only; runtime policy is unchanged. [Replacement policy](../../../requirements-09-minimal-evidence/proposal.md).

## MODIFIED Requirements

### Requirement: Policy Engine

Policy evaluation outputs SHALL be serializable into governance evidence records.

#### Scenario: Policy rule results include evidence-ready fields

- **GIVEN** policy validation completes
- **WHEN** evidence serialization runs
- **THEN** each rule result includes rule ID, severity, mode, and outcome
- **AND** output can be consumed by CI gates without additional transformation.
