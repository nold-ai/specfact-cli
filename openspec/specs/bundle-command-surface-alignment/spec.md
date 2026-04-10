# bundle-command-surface-alignment Specification

## Purpose

TBD - created by archiving change module-migration-10-bundle-command-surface-alignment. Update Purpose after archive.

## Requirements

### Requirement: Documented Grouped Commands Must Resolve In Installed Official Bundles

The system SHALL ensure that grouped CLI commands documented for a shipped release resolve in an environment where the corresponding official bundles are installed.

#### Scenario: Documented project subgroup commands resolve

- **GIVEN** the official `nold-ai/specfact-project` bundle is installed
- **WHEN** the user runs documented grouped command paths such as `specfact code import --help` or `specfact project plan review --help`
- **THEN** the command path resolves successfully from the installed bundle runtime
- **AND** the help output reflects the mounted subgroup command rather than `No such command`.

#### Scenario: Documented spec subgroup commands resolve

- **GIVEN** the official `nold-ai/specfact-spec` bundle is installed
- **WHEN** the user runs documented grouped command paths such as `specfact spec generate contracts-prompt --help` or `specfact spec contract test --help`
- **THEN** the command path resolves successfully from the installed bundle runtime
- **AND** the installed bundle help tree exposes those subgroup commands.

### Requirement: Release Documentation Must Not Promise Missing Grouped Commands

The system SHALL keep release-facing documentation aligned with the actual shipped grouped command surface.

#### Scenario: Unsupported path is removed from docs

- **GIVEN** a grouped command path is not part of the shipped runtime surface for the current release
- **WHEN** release-facing docs are updated
- **THEN** that path is removed or corrected in README/docs/release content
- **AND** users are not told to run a command that fails at runtime.

#### Scenario: Slash prompts do not hide missing CLI registration

- **GIVEN** a grouped CLI command is documented as part of the release surface
- **WHEN** corresponding slash-command guidance exists
- **THEN** the docs may include the slash prompt as an IDE workflow aid
- **BUT NOT** as a substitute for a missing or unregistered CLI path.

### Requirement: Runtime Validation Detects Documented Command Drift

The system SHALL fail validation when a documented grouped command path is missing from the installed official bundle command tree.

#### Scenario: Missing documented grouped command fails validation

- **GIVEN** a documented grouped command inventory for the shipped release
- **AND** the official bundle install/runtime validation environment
- **WHEN** a documented grouped command path is not mounted by the installed bundle
- **THEN** validation fails with the missing command path and owning bundle id
- **AND** the report distinguishes this from help-only or docs-only command coverage.
