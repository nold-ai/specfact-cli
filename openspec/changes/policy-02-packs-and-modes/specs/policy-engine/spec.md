## MODIFIED Requirements

### Requirement: Policy Engine
The policy engine SHALL support advisory, mixed, and hard enforcement modes with per-rule overrides.

#### Scenario: Advisory mode never blocks
- **GIVEN** policy mode is advisory
- **WHEN** violations are found
- **THEN** command exits successfully
- **AND** violations are emitted as warnings/annotations.

#### Scenario: Mixed mode applies per-rule blocking semantics
- **GIVEN** mode is mixed and rule severity map marks one rule as blocking
- **WHEN** that rule fails
- **THEN** command exits non-zero
- **AND** non-blocking rule failures remain advisory.

#### Scenario: Clean-code rules use policy-engine mode mapping
- **GIVEN** the `specfact/clean-code-principles` pack is installed with mixed mode
- **WHEN** a clean-code rule such as `banned-generic-public-names` is overridden to `hard`
- **THEN** the policy engine evaluates that rule as blocking
- **AND** other clean-code rules continue using their configured per-rule modes
