## ADDED Requirements

### Requirement: Unified Security Finding Model

The system SHALL define a single `SecurityFinding` model accepted across all security categories.

#### Scenario: Finding carries category-appropriate optional fields

- **GIVEN** a finding with `category: sca` and a CVE identifier
- **WHEN** the model validates
- **THEN** `cve` and `cvss_score` are accepted
- **AND** `spdx_license`, `pii_type`, `gdpr_article` are absent.

#### Scenario: Category-specific field required for its category

- **GIVEN** a finding with `category: license` and no `spdx_license`
- **WHEN** the model validates
- **THEN** validation fails with a clear field-required error.

#### Scenario: Fingerprint uniquely identifies a finding

- **GIVEN** two scans producing the same underlying finding
- **WHEN** fingerprints are computed
- **THEN** both fingerprints are identical
- **AND** dedup against prior-scan evidence works via fingerprint lookup.

### Requirement: Canonical CVSS → Severity Mapping

The system SHALL map CVSS v3.1 scores to the review severity enum via a fixed table.

#### Scenario: Critical CVSS maps to blocker

- **GIVEN** a finding with `cvss_score: 9.2`
- **WHEN** the scorer normalises severity
- **THEN** severity is `blocker`.

#### Scenario: Profile override can down-rate but not up-rate

- **GIVEN** a profile override attempts to up-rate a `low` to `blocker` without explicit policy
- **WHEN** the scorer applies profile overrides
- **THEN** the up-rate is rejected
- **AND** the scorer logs the rejection with the policy rule-id needed to authorise it.

### Requirement: Security Policy Pack Namespace

The system SHALL accept `security/` rule packs in the policy engine with allow/deny lists per sub-category.

#### Scenario: Deny-listed SPDX license blocks the run

- **GIVEN** a policy pack denying `GPL-3.0` and an SBOM contains a GPL-3.0 dependency
- **WHEN** `specfact review security --category license` runs in `hard` mode
- **THEN** exit code is 1
- **AND** the report includes the license finding with the violated policy rule-id.

#### Scenario: Advisory mode reports but does not fail

- **GIVEN** the same policy pack in `advisory` mode
- **WHEN** the run completes
- **THEN** exit code is 0
- **AND** the finding is present in the report.

### Requirement: Security Review CLI Command

The system SHALL provide `specfact review security` with category filtering and shared-envelope output.

#### Scenario: Category filter limits run scope

- **GIVEN** `--category secret`
- **WHEN** the command runs
- **THEN** only secret-scanning runners are invoked
- **AND** the report contains only `secret` findings.

#### Scenario: JSON output conforms to shared envelope

- **GIVEN** `--report json`
- **WHEN** the command completes
- **THEN** the `security` top-level section appears in the shared `ReviewReport`
- **AND** existing sections (code_quality, resiliency) are unaffected.

### Requirement: ReviewReport envelope evolution

The shared `ReviewReport` envelope SHALL carry an explicit `schema_version` string for `--report json` outputs.

#### Scenario: Unknown top-level sections are tolerated by default

- **GIVEN** a consumer parses `ReviewReport` JSON from `specfact review security --report json`
- **WHEN** the payload includes top-level sections the consumer does not recognize
- **THEN** the consumer SHALL ignore unknown sections by default (unknown-section tolerance) while still validating
  required keys for the sections it understands
- **AND** consumers MAY opt into strict mode that fails on unknown sections only when pinned to a matching
  `schema_version`.

#### Scenario: Stable pillar keys require coordinated bumps

- **GIVEN** stable pillar keys such as `security`, `code_quality`, and `resiliency`
- **WHEN** their shapes change incompatibly
- **THEN** emitters MUST bump `schema_version` according to the published semver policy for `review-report-model`
- **AND** additive fields inside a pillar MAY ship without a major bump when parsers remain backward compatible.
