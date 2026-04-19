## ADDED Requirements

### Requirement: GDPR Baseline Policy Pack

The system SHALL provide a core GDPR baseline policy pack defining lawful basis, residency, retention, deletion, and breach-handling controls.

#### Scenario: Baseline pack defines lawful basis requirements

- **WHEN** a privacy/security profile loads the GDPR baseline pack
- **THEN** the pack defines allowed lawful basis values for personal-data processing
- **AND** missing lawful basis metadata is treated according to the active enforcement mode.

#### Scenario: Baseline pack defines data subject rights controls

- **WHEN** a bundle emits findings related to erasure, access, rectification, or retention
- **THEN** the baseline pack can map those findings to explicit policy keys
- **AND** downstream evidence uses the same vocabulary across bundles.

### Requirement: Residency Allowlist Enforcement

The system SHALL support EU residency allowlists for model endpoints, evidence stores, and exporters.

#### Scenario: Non-EU residency target is flagged

- **GIVEN** the active baseline allows only EU residency targets
- **WHEN** a configured target resolves to a non-EU region
- **THEN** the policy engine emits or preserves a GDPR finding carrying residency metadata
- **AND** hard mode can fail the run.

#### Scenario: Advisory mode preserves finding without blocking

- **GIVEN** the profile enforcement mode is advisory
- **WHEN** a residency violation is detected
- **THEN** the finding is reported with GDPR metadata
- **AND** the exit code remains non-blocking.
