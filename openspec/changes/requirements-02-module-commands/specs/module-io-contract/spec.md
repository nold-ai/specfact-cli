## MODIFIED Requirements

### Requirement: Module Io Contract
The requirements module SHALL implement all `ModuleIOContract` operations.

#### Scenario: Import operation maps backlog items to requirements
- **GIVEN** backlog input for import
- **WHEN** `import_to_bundle` runs
- **THEN** requirements are added to the bundle with stable IDs
- **AND** parse diagnostics are included for partial failures.

#### Scenario: Validate operation enforces profile schema
- **GIVEN** requirements bundle and active profile schema
- **WHEN** `validate_bundle` runs
- **THEN** missing required fields are reported
- **AND** validation severity respects active policy mode.
