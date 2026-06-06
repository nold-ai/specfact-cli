## ADDED Requirements

### Requirement: Install Reconciles Existing Module Availability

When a user installs a module whose artifact already exists in the selected scope, the system SHALL reconcile the artifact with lifecycle state and runtime availability before reporting success.

#### Scenario: Existing installed module is disabled

- **GIVEN** a module artifact exists under the selected install scope
- **AND** the module state file marks the manifest module id as disabled
- **WHEN** the user runs `specfact module install <module-id>`
- **THEN** the command SHALL NOT report only that the module is already installed
- **AND** the command SHALL either enable that module for the user-requested install or print an explicit installed-but-disabled diagnostic with `specfact module enable <manifest-module-id>`

#### Scenario: Existing installed module is skipped by runtime eligibility checks

- **GIVEN** a module artifact exists under the selected install scope
- **AND** runtime registration would skip that module because of compatibility, dependency, schema, or integrity validation
- **WHEN** the user runs `specfact module install <module-id>`
- **THEN** the command SHALL report the specific local reason that the module is installed but unavailable
- **AND** the command SHALL include a recovery action such as reinstall, enable dependency modules, update SpecFact CLI, or inspect origins

#### Scenario: Existing installed module is available

- **GIVEN** a module artifact exists under the selected install scope
- **AND** lifecycle state and runtime eligibility allow its command group to register
- **WHEN** the user runs `specfact module install <module-id>`
- **THEN** the command MAY skip reinstalling the artifact
- **AND** the command SHALL report that the module is already installed and available from the selected scope

## MODIFIED Requirements

### Requirement: Missing Command Diagnostics Explain Installed-Unavailable Causes

When a known module-provided command group is not registered, the system SHALL distinguish an absent module from an installed module that is unavailable for another local reason.

#### Scenario: Missing command is provided by disabled module

- **GIVEN** a known command group is provided by a discovered module
- **AND** that module is disabled in lifecycle state
- **WHEN** the user invokes the command group
- **THEN** the CLI SHALL report that the module is installed but disabled
- **AND** the CLI SHALL include `specfact module enable <manifest-module-id>` guidance

#### Scenario: Missing command is provided by skipped module

- **GIVEN** a known command group is provided by a discovered module
- **AND** command registration skipped the module for compatibility, dependency, schema, or integrity reasons
- **WHEN** the user invokes the command group
- **THEN** the CLI SHALL report that the module is installed but unavailable
- **AND** the CLI SHALL include the specific skipped reason when it can be derived without importing the module command app

#### Scenario: Missing command has no discovered provider

- **GIVEN** no discovered module provider exists for a known command group
- **WHEN** the user invokes the command group
- **THEN** the CLI SHALL keep reporting that the module is not installed
- **AND** the CLI SHALL include install or init profile guidance

## ADDED Requirements: Canonical Module Identity

### Requirement: Module Install Uses Canonical Module Identity

The system SHALL resolve install requests, discovered manifest IDs, and lifecycle state rows to a canonical module identity before deciding whether an install is already satisfied.

#### Scenario: Bare name resolves to installed marketplace manifest id

- **GIVEN** `~/.specfact/modules/specfact-codebase/module-package.yaml` declares `name: nold-ai/specfact-codebase`
- **WHEN** the user runs `specfact module install specfact-codebase`
- **THEN** the command SHALL treat `specfact-codebase` and `nold-ai/specfact-codebase` as the same installed module for lifecycle-state checks
- **AND** any state update or enable guidance SHALL use `nold-ai/specfact-codebase`

#### Scenario: Legacy namespace request resolves to installed marketplace manifest id

- **GIVEN** an installed module manifest declares `name: nold-ai/specfact-codebase`
- **WHEN** the user runs `specfact module install specfact/specfact-codebase`
- **THEN** the command SHALL NOT create or require a duplicate lifecycle state entry for `specfact/specfact-codebase`
- **AND** the command SHALL explain the canonical installed module identity if it skips installation
