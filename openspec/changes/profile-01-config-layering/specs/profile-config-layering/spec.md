## ADDED Requirements

### Requirement: Profile Config Layering
The system SHALL resolve configuration using deterministic layer precedence.

#### Scenario: Layer precedence is deterministic
- **GIVEN** values are present in profile defaults, org baseline, repo overlay, and developer-local override
- **WHEN** configuration is resolved
- **THEN** precedence is `profile defaults < org baseline < repo overlay < developer local`
- **AND** the resolved output records the winning source for each key.

#### Scenario: Profile-specific defaults are applied
- **GIVEN** `specfact init --profile enterprise`
- **WHEN** profile config is generated
- **THEN** policy mode defaults to enterprise-grade enforcement
- **AND** requirements schema includes enterprise-required fields.

#### Scenario: Invalid profile is rejected
- **GIVEN** `specfact init --profile unknown`
- **WHEN** command validation runs
- **THEN** the command exits with a validation error
- **AND** output lists supported profile values.
