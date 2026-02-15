## ADDED Requirements

### Requirement: Central Config Sources
The system SHALL support read-only central configuration sources with local overlays.

#### Scenario: Pull read-only baseline from central source
- **GIVEN** `.specfact/profile.yaml` defines a central git config source
- **WHEN** profile resolution runs
- **THEN** baseline values are loaded from that source
- **AND** baseline files are treated as read-only inputs.

#### Scenario: Local overlay overrides baseline
- **GIVEN** baseline sets `policy_mode: advisory`
- **AND** repo overlay sets `policy_mode: mixed`
- **WHEN** configuration is resolved
- **THEN** the resolved mode is `mixed`
- **AND** output includes baseline-versus-overlay provenance.

#### Scenario: Divergence warning is emitted
- **GIVEN** local values diverge from central baseline policy keys
- **WHEN** config check runs
- **THEN** the system emits a divergence warning
- **AND** the warning includes source key paths that differ.
