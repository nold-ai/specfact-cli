# module-owned-ide-prompts Specification

## Purpose
TBD - created by archiving change packaging-02-cross-platform-runtime-and-module-resources. Update Purpose after archive.
## Requirements
### Requirement: IDE prompt export SHALL use installed module resources
`specfact init ide` SHALL discover prompt templates from installed module packages and their packaged resource directories. The export flow SHALL not depend on workflow prompt files stored under the core CLI package for bundle-owned commands.

#### Scenario: Installed bundle contributes prompt resources
- **WHEN** an installed module exposes packaged prompt resources for IDE export
- **THEN** `specfact init ide` discovers that module's prompt directory from the installed module location
- **AND** copies the prompt files from that module-owned resource path into the selected IDE folder

#### Scenario: Core package does not masquerade as owner of bundle prompts
- **WHEN** workflow prompts exist only for bundle/module-owned commands
- **THEN** the export catalog excludes equivalent core-owned fallback prompt files
- **AND** prompt provenance remains attributable to the owning module

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

