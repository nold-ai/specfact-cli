# module-owned-ide-prompts Specification

## Purpose

TBD - created by archiving change packaging-02-cross-platform-runtime-and-module-resources. Update Purpose after archive.
## Requirements
### Requirement: IDE prompt export SHALL use installed module resources

`specfact init ide` SHALL discover prompt templates from installed module packages and their packaged resource directories. The export flow SHALL not depend on workflow prompt files stored under the core CLI package for bundle-owned commands.

#### Scenario: IDE setup accepts explicit environment manager

- **GIVEN** prompt templates are available for export
- **WHEN** the user runs `specfact init ide --env-manager uv`
- **THEN** IDE prompt export uses the selected `uv` environment manager metadata for dependency setup decisions
- **AND** the command does not emit the "No Compatible Environment Manager Detected" warning for that explicit manager

### Requirement: Missing prompt assets SHALL fail clearly

If a selected or installed module is expected to provide prompt resources but no packaged prompt directory is available, `specfact init ide` SHALL report an actionable error or warning that identifies the owning module and the missing resource path.

#### Scenario: Selected module has no packaged prompt directory

- **WHEN** `specfact init ide` evaluates an installed module that should contribute prompts but its packaged prompt resource directory is absent
- **THEN** the command reports which module is incomplete
- **AND** the message explains that prompt resources must ship with the owning module package

#### Scenario: Prompt discovery feeds later source selection

- **WHEN** the prompt export catalog is built for a repository with multiple installed modules
- **THEN** the discovered prompt sources are available for later interactive or non-interactive source selection features
- **AND** the catalog preserves module-level provenance for each exported prompt

### Requirement: Core init flows SHALL use installed module-owned template resources

When a setup or install flow needs a non-prompt resource that is owned by an extracted bundle, the core CLI SHALL resolve that asset from the installed bundle package instead of from a core-owned fallback directory.

#### Scenario: Backlog field mapping templates resolve from installed backlog bundle

- **WHEN** a core init or setup flow needs backlog field mapping templates
- **THEN** the CLI resolves those templates from the installed backlog bundle resource path
- **AND** the flow does not require a canonical source copy under the core CLI repository

#### Scenario: Missing module-owned template asset fails clearly

- **WHEN** a required installed bundle resource path for a module-owned template is absent
- **THEN** the CLI reports which bundle-owned asset is missing
- **AND** the message directs the user toward installing or updating the owning bundle

### Requirement: Core materialization of module-owned IDE assets SHALL use safe project writes

When core setup flows materialize module-owned IDE assets into a user repository, they SHALL route all local file mutations through the core safe-write policy.

#### Scenario: Module-owned prompt export uses safe-write helper for settings mutation

- **WHEN** `specfact init ide` exports bundle-owned prompt files and updates a related IDE config artifact
- **THEN** the config mutation SHALL use the safe-write helper with declared ownership metadata
- **AND** the command SHALL preserve unrelated user-managed content in the target artifact

#### Scenario: Module-owned template copy does not silently replace existing user customization

- **WHEN** a core setup flow copies a module-owned template asset into a target path that already exists in the user repository
- **THEN** the flow SHALL skip, merge, or require explicit replacement according to the declared safe-write mode
- **AND** SHALL NOT silently overwrite the existing file

