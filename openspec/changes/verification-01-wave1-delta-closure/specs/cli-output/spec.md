## MODIFIED Requirements

### Requirement: Command Reference Completeness

The system SHALL keep command reference documentation aligned with shipped CLI command surfaces for each release.

#### Scenario: Shipped patch command documented in command reference

- **GIVEN** `specfact patch` command group is available in release builds
- **WHEN** command reference documentation is published for that release
- **THEN** reference docs include `specfact patch apply` options and usage semantics
- **AND** docs do not describe unavailable command variants as fully implemented behavior.

### Requirement: Changelog Release Integrity

The project SHALL maintain one canonical section per released version and accurate placement of released capabilities.

#### Scenario: Release section has no duplicate version headers

- **GIVEN** release `v0.34.0` is merged and published
- **WHEN** maintainers review `CHANGELOG.md`
- **THEN** there is a single `0.34.0` section
- **AND** features shipped in that release are listed under that release (not left under `Unreleased`).
