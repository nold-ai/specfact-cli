## ADDED Requirements

### Requirement: GDPR Baseline Policy Pack

The system SHALL provide a core GDPR baseline policy pack defining lawful basis, residency, retention, deletion, and breach-handling controls.

#### Scenario: Baseline pack defines lawful basis requirements

- **WHEN** a privacy/security profile loads the GDPR baseline pack
- **THEN** the pack defines allowed lawful basis values for personal-data processing
- **AND** missing lawful basis metadata is treated according to the active enforcement mode.

#### Scenario: Lawful basis metadata is validated against an explicit enumeration

- **GIVEN** processing metadata includes a `lawful_basis` field
- **WHEN** the baseline validates the field
- **THEN** only the values `consent`, `contract`, `legal_obligation`, `vital_interests`, `public_task`, and
  `legitimate_interests` are accepted
- **AND** any other value produces a validation finding.

#### Scenario: Missing lawful basis is a blocker in hard enforcement

- **GIVEN** `lawful_basis` metadata is missing for personal-data processing covered by the baseline
- **WHEN** enforcement mode is `hard`
- **THEN** a **blocker** finding is emitted referencing the missing `lawful_basis` metadata.

#### Scenario: Missing lawful basis is advisory-only in advisory enforcement

- **GIVEN** `lawful_basis` metadata is missing for personal-data processing covered by the baseline
- **WHEN** enforcement mode is `advisory`
- **THEN** an **advisory** finding is emitted referencing the missing `lawful_basis` metadata
- **AND** execution is not blocked solely for this omission.

#### Scenario: Baseline pack defines data subject rights controls

- **WHEN** a bundle emits findings related to erasure, access, rectification, or retention
- **THEN** the baseline pack can map those findings to explicit policy keys
- **AND** downstream evidence uses the same vocabulary across bundles.

### Requirement: Residency Allowlist Enforcement

The system SHALL support EU residency allowlists for model endpoints, evidence stores, and exporters using a canonical
structure: an **allowlist array** of **ISO 3166-1 alpha-2** country codes (with optional provider-specific region tags
documented in a mapping table that MUST normalize to ISO codes for comparison).

#### Scenario: EU residency allowlist is defined by ISO region codes

- **GIVEN** the baseline allowlist is expressed as ISO alpha-2 codes for current EU member states (official membership
  list + codes, versioned with the pack)
- **WHEN** a configured target resolves to a region code present in the allowlist
- **THEN** no `data_residency` blocker is emitted for residency alone
- **AND** when resolution is impossible, the engine emits a `data_residency` finding with `region: unknown` and
  attaches the best-known metadata available to scanners.

#### Scenario: Multi-region or global services are classified explicitly

- **GIVEN** a target advertises multiple regions or a global footprint without a single ISO anchor
- **WHEN** residency classification runs
- **THEN** the target is treated as **multi-region** and a `data_residency` finding is emitted describing the ambiguity
- **AND** `hard` mode MAY fail the run when the baseline requires a single-region EU anchor.

#### Scenario: Non-EU residency target is flagged

- **GIVEN** the active baseline allows only EU residency targets
- **WHEN** a configured target resolves to a non-EU region
- **THEN** the policy engine emits or preserves a GDPR finding carrying residency metadata (including ISO or mapped
  region code when known)
- **AND** hard mode can fail the run.

#### Scenario: Advisory mode preserves finding without blocking

- **GIVEN** the profile enforcement mode is advisory
- **WHEN** a residency violation is detected
- **THEN** the finding is reported with GDPR metadata
- **AND** the exit code remains non-blocking.

#### Scenario: Missing residency metadata surfaces unknown region

- **GIVEN** residency metadata is unavailable for a configured exporter or model endpoint
- **WHEN** enforcement evaluates the target
- **THEN** the engine emits a `data_residency` finding with `region: unknown`
- **AND** `hard` mode MAY fail the run when the baseline mandates explicit residency proof.
