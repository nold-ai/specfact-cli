## ADDED Requirements

### Requirement: Requirements Module IO Contract

Requirements implementations SHALL consume core requirements context adapter
helpers through the existing `ModuleIOContract` boundary.

#### Scenario: Import operation maps backlog items to requirements

- **GIVEN** source-attributed requirement records imported by a module
- **WHEN** `import_to_bundle` stores normalized requirements on a `ProjectBundle`
- **THEN** requirements are added under the `requirements.inputs` extension with stable IDs
- **AND** parse diagnostics remain available to the module runtime for partial failures.

#### Scenario: Validate operation enforces profile schema

- **GIVEN** a requirements bundle and active validation profile
- **WHEN** `validate_bundle` delegates to core requirements context validation
- **THEN** missing evidence links and weak context are reported
- **AND** validation severity respects the selected evidence strictness profile.

#### Scenario: Requirements runtime mounts through grouped module metadata

- **GIVEN** a paired requirements runtime package with category `requirements`
- **WHEN** module metadata is discovered by core registry validation
- **THEN** the `requirements` category is accepted with group command `requirements`
- **AND** root CLI command handlers remain owned by the paired requirements runtime.

#### Scenario: Installed requirements runtime is callable from the root CLI

- **GIVEN** the paired requirements runtime package is installed and enabled
- **AND** the package exposes a native `requirements` command app
- **WHEN** the root SpecFact CLI is rebuilt from discovered module metadata
- **THEN** `specfact requirements --help` resolves through the installed module app
- **AND** missing `requirements` installs show marketplace recovery guidance for `nold-ai/specfact-requirements`.
