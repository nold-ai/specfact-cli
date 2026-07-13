## MODIFIED Requirements

### Requirement: Requirements Context Adapter

The system SHALL provide core requirements context adapter helpers for import,
normalization, validation, and coverage inspection of upstream requirement
context as validation evidence. Import SHALL support native OpenSpec change
folders and Spec Kit feature folders as first-class sources in addition to
generic record files, and validation SHALL evaluate deterministic pass/fail
gate categories with profile-driven severity.

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

#### Pending paired-module follow-up

The `specfact requirements import --from-openspec` and `--from-speckit`
command flags, auto-detection, persistence, and diagnostic rendering remain
unimplemented in the requirements module. They are owned by
`nold-ai/specfact-cli-modules#168`; this core change supplies only the helpers
that the future module runtime will call. Until that module release declares a
core compatibility floor of `0.52.0`, `--from-file` is the only shipped module
import path.

#### Scenario: Unverified scenarios gate validation

- **GIVEN** an imported requirement whose business rules have no `test` or `validation` evidence link
- **WHEN** requirements context validation runs under a profile that treats `scenario-unverified` as an error
- **THEN** the validation report contains a `scenario-unverified` finding naming the requirement and rule IDs
- **AND** the command exits non-zero.

#### Scenario: Stale imports gate validation

- **GIVEN** an imported requirement whose source `revision` content hash no longer matches the artifact on disk
- **WHEN** requirements context validation runs
- **THEN** the validation report contains a `stale-import` finding with the source locator
- **AND** profile severity decides whether the run fails.

#### Scenario: Missing sources gate validation

- **GIVEN** an imported requirement whose source locator no longer resolves to an existing artifact
- **WHEN** requirements context validation runs
- **THEN** the validation report contains a `source-missing` finding with the unresolved locator.

#### Scenario: Relative source locators resolve from the project root

- **GIVEN** an imported requirement stores a relative source locator
- **WHEN** validation runs with its project root from a different process directory
- **THEN** the locator is resolved relative to that project root for missing-source and staleness checks.

#### Scenario: Omitted profile resolves from layered configuration

- **GIVEN** a project whose layered configuration (profile defaults, org baseline, repo overlay, developer local) resolves to a validation profile
- **WHEN** requirements context validation runs without an explicit profile argument
- **THEN** the resolved configured profile decides gate severity instead of a hardcoded default
- **AND** an explicitly passed profile argument overrides the configured profile.
- **AND** profile-derived `requirements_schema` values from configured layers
  do not override the explicitly selected profile defaults.

#### Scenario: Profile required fields use evidence-compatible aliases

- **GIVEN** a resolved profile whose `requirements_schema.required_fields`
  contains `id`, `title`, `acceptance`, `trace_links`, and a field unsupported
  by `RequirementInput`
- **WHEN** requirements context validation runs
- **THEN** `id`, `title`, `acceptance`, and `trace_links` evaluate
  `requirement_id`, `title`, `business_rules`, and `evidence_links`,
  respectively, for completeness findings
- **AND** the unsupported field produces a machine-readable
  `unsupported-profile-field` advisory
- **AND** native imported records are not marked incomplete solely because the
  upstream artifact has no owner, risk, or exception metadata.

#### Scenario: Ambiguous mappings gate validation

- **GIVEN** two imported requirements that claim the same derived requirement identity from different sources
- **WHEN** requirements context validation runs
- **THEN** the validation report contains an `ambiguous-mapping` finding naming both source locators
- **AND** no record is silently dropped or overwritten.

#### Scenario: Unsupported source format blocks module import

- **GIVEN** a module import request whose OpenSpec schema or Spec Kit template
  profile is not supported by the core evidence adapter
- **WHEN** the module delegates import to core
- **THEN** it surfaces the core `unsupported-source-schema` diagnostic without
  creating or persisting partial requirement records
- **AND** it does not implement provider-version detection or fallback parsing.
