## ADDED Requirements

### Requirement: Profile Config Layering

The system SHALL resolve configuration using deterministic layer precedence.

#### Scenario: Layer precedence is deterministic

- **GIVEN** values are present in profile defaults, org baseline, repo overlay, and developer-local override
- **WHEN** configuration is resolved
- **THEN** precedence is `profile defaults < org baseline < repo overlay < developer local`
- **AND** the resolved output records the winning source for each key.

#### Scenario: Profile-specific defaults are applied

- **GIVEN** `specfact init --profile solo`, `startup`, `mid_size`, or `enterprise`
- **WHEN** profile config is generated
- **THEN** the selected tier provides deterministic defaults for validation severity, policy mode, evidence persistence, clean-code mode, module activation, and requirements schema
- **AND** enterprise defaults include enterprise-required requirements schema fields.

#### Scenario: Clean-code defaults are inherited from the selected tier

- **GIVEN** profile defaults are generated for `solo`, `startup`, `mid_size`, and `enterprise`
- **WHEN** profile config is generated
- **THEN** clean-code defaults are `solo -> advisory`, `startup -> advisory_then_mixed`, `mid_size -> mixed`, and `enterprise -> hard`
- **AND** no separate clean-code profile selector is required in the resolved config

#### Scenario: Invalid profile is rejected

- **GIVEN** `specfact init --profile unknown`
- **WHEN** command validation runs
- **THEN** the command exits with a validation error
- **AND** output lists supported profile values.
