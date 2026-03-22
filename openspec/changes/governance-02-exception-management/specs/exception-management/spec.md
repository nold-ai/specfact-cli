## ADDED Requirements

### Requirement: Exception Management
The system SHALL support explicit, tracked, and time-bound governance exceptions.

#### Scenario: Active exception suppresses blocking until expiry
- **GIVEN** `.specfact/exceptions.yaml` contains an active exception for a policy and scope
- **WHEN** policy validation runs before expiration
- **THEN** matching violation is downgraded from blocking to non-blocking
- **AND** evidence records the applied exception ID.

#### Scenario: Expired exception restores blocking behavior
- **GIVEN** exception expiry date is in the past
- **WHEN** matching policy violation occurs
- **THEN** violation is treated per normal mode semantics
- **AND** output identifies the exception as expired.

#### Scenario: Clean-code exceptions target policy rule identifiers
- **GIVEN** `.specfact/exceptions.yaml` contains `policy: clean-code-principles/banned-generic-public-names`
- **WHEN** a matching naming finding is emitted within the declared scope
- **THEN** that specific rule is suppressed according to the exception lifecycle
- **AND** no separate `principle` field is required in the exception schema
