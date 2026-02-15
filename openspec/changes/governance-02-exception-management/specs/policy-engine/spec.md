## MODIFIED Requirements

### Requirement: Policy Engine
Policy evaluation SHALL apply scoped exceptions before computing final blocking outcome.

#### Scenario: Scope mismatch does not suppress violation
- **GIVEN** exception exists for a different scope than the evaluated artifact
- **WHEN** policy rule fails
- **THEN** violation is not suppressed
- **AND** engine reports scope mismatch diagnostics.
