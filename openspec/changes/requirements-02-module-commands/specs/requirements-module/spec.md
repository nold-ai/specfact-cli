## ADDED Requirements

### Requirement: Requirements Context Adapter

The system SHALL provide core requirements context adapter helpers for import,
normalization, validation, and coverage inspection of upstream requirement
context as validation evidence.

#### Scenario: Import helpers normalize source-attributed records

- **GIVEN** upstream requirement-like records with source references
- **WHEN** requirements context normalization runs
- **THEN** valid records are returned as `RequirementInput` instances
- **AND** each record keeps schema version and source attribution.

#### Scenario: Invalid imported records produce bounded diagnostics

- **GIVEN** one valid upstream record and one malformed upstream record
- **WHEN** requirements context normalization runs
- **THEN** valid records are preserved
- **AND** the malformed record is reported as a diagnostic without free-form planning prose.

#### Scenario: Validation and coverage expose evidence usefulness

- **GIVEN** normalized requirement inputs on a `ProjectBundle`
- **WHEN** requirements context validation and coverage inspection run
- **THEN** bundle-level completeness and coverage counts are reported with missing-evidence requirement IDs
- **AND** the result is machine-readable for downstream module commands.
