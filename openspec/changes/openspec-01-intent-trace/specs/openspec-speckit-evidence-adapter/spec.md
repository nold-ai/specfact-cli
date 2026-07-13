## ADDED Requirements

### Requirement: OpenSpec Change Folder Import

The system SHALL deterministically import native OpenSpec change folders
(`proposal.md`, `specs/*/spec.md`, `tasks.md`) into normalized
`RequirementInput` records without requiring any SpecFact-specific metadata in
the upstream artifacts.

#### Scenario: OpenSpec spec delta requirements become requirement inputs

- **GIVEN** an OpenSpec change folder whose `specs/<capability>/spec.md`
  contains requirements with GIVEN/WHEN/THEN scenarios
- **WHEN** the OpenSpec import runs against that change folder
- **THEN** each spec requirement produces a `RequirementInput` with a stable
  derived `requirement_id` of the form `openspec:<change-id>:<capability>:<requirement-slug>`
- **AND** repeated titles that derive the same slug receive a deterministic
  ordinal suffix so every record in one import has a unique identity
- **AND** each scenario is normalized into a `BusinessRule` with its given,
  when, and then clauses preserved
- **AND** each record carries a `RequirementSourceReference` with
  `source_type` `openspec_change` and a locator pointing at the parsed artifact

#### Scenario: Import requires no upstream metadata

- **GIVEN** an OpenSpec change folder with no SpecFact-specific sections or
  metadata of any kind
- **WHEN** the OpenSpec import runs
- **THEN** the import succeeds using only the native OpenSpec artifact
  structure
- **AND** no warning or advisory about missing SpecFact metadata is emitted

#### Scenario: Re-import of unchanged artifacts is idempotent

- **GIVEN** a bundle that already contains records imported from an OpenSpec
  change folder
- **WHEN** the same unchanged change folder is imported again
- **THEN** the resulting requirement records are identical to the prior import
- **AND** no duplicate records are created

### Requirement: Spec Kit Feature Folder Import

The system SHALL deterministically import native Spec Kit feature folders
(`spec.md`, `plan.md`, `tasks.md`) into normalized `RequirementInput` records
without requiring any SpecFact-specific metadata in the upstream artifacts.

#### Scenario: Spec Kit spec requirements become requirement inputs

- **GIVEN** a Spec Kit feature folder containing a `spec.md` with functional
  requirements and acceptance scenarios
- **WHEN** the Spec Kit import runs against that feature folder
- **THEN** each requirement produces a `RequirementInput` with a stable derived
  `requirement_id` of the form `speckit:<feature-dir>:<requirement-slug>`
- **AND** repeated requirement text that derives the same slug receives a
  deterministic ordinal suffix so every record in one import has a unique identity
- **AND** acceptance scenarios are normalized into `BusinessRule` records
- **AND** each record carries a `RequirementSourceReference` with
  `source_type` `speckit_spec`

### Requirement: Content-Hash Source Attribution

Importers for OpenSpec and Spec Kit artifacts SHALL populate each
`RequirementSourceReference.revision` with a content hash of the parsed
artifact using the `sha256:<hex>` convention, so staleness is mechanically
detectable.

#### Scenario: Imported source references carry a content hash

- **GIVEN** an OpenSpec or Spec Kit artifact being imported
- **WHEN** the import produces a `RequirementSourceReference`
- **THEN** the reference `revision` is set to `sha256:` followed by the SHA-256
  hex digest of the artifact content at import time

#### Scenario: Non-hash revisions remain opaque

- **GIVEN** a requirement record whose source `revision` does not start with
  `sha256:`
- **WHEN** staleness evaluation runs
- **THEN** the record is exempt from content-hash staleness checks
- **AND** no finding is produced solely because the revision is not a hash

### Requirement: Read-Only Upstream Guarantee

The import path SHALL never create, modify, or delete files inside upstream
OpenSpec or Spec Kit directories.

#### Scenario: Import leaves upstream artifacts untouched

- **GIVEN** an OpenSpec change folder and a Spec Kit feature folder used as
  import sources
- **WHEN** import, validation, and coverage inspection run to completion
- **THEN** the byte content and file listing of the upstream directories are
  unchanged

### Requirement: Fail-Closed Source Compatibility

The system SHALL import only explicitly tested native source-format profiles
and SHALL reject unrecognized or customized source schemas before emitting any
requirement records. Compatibility SHALL be structural because upstream
artifacts do not provide a dependable universal tool-version field.

#### Scenario: Default OpenSpec schema is accepted

- **GIVEN** an OpenSpec change using the default `spec-driven` schema (or no
  explicit schema) and native requirement/scenario Markdown headings
- **WHEN** the OpenSpec import runs
- **THEN** the source is accepted by compatibility preflight
- **AND** normalization proceeds using the default OpenSpec profile.

#### Scenario: Custom OpenSpec schema is rejected without partial records

- **GIVEN** an OpenSpec change whose project or change configuration declares
  a schema other than the tested default, or declares a non-string schema value
- **WHEN** the OpenSpec import runs
- **THEN** the result contains an error diagnostic with code
  `unsupported-source-schema`
- **AND** the result contains no requirement records from that source.

#### Scenario: Customized Spec Kit templates are rejected without partial records

- **GIVEN** a Spec Kit feature under a project with template overrides,
  presets, or extension template roots
- **WHEN** the Spec Kit import runs
- **THEN** the result contains an error diagnostic with code
  `unsupported-source-schema`
- **AND** the result contains no requirement records from that source.

#### Scenario: Unrecognized default-format markers are rejected

- **GIVEN** an OpenSpec or Spec Kit source that does not contain the required
  headings of its tested default Markdown profile
- **WHEN** the importer preflights the source
- **THEN** it emits `unsupported-source-schema`
- **AND** it does not guess a mapping, fetch upstream definitions, or emit a
  partial import.
