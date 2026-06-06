# module-installation Specification

## Purpose

TBD - created by archiving change marketplace-01-central-module-registry. Update Purpose after archive.
## Requirements
### Requirement: Install command downloads and installs modules

The system SHALL provide `specfact module install <module-id>` command that downloads, verifies, and installs modules from the registry.

#### Scenario: Install module from marketplace

- **WHEN** user runs `specfact module install specfact/backlog`
- **THEN** system SHALL fetch registry index
- **AND** SHALL download module tarball
- **AND** SHALL verify checksum
- **AND** SHALL extract to ~/.specfact/marketplace-modules/backlog/
- **AND** SHALL register module
- **AND** SHALL display success message

#### Scenario: Install specific version

- **WHEN** user runs `specfact module install specfact/backlog --version 0.29.0`
- **THEN** system SHALL install specified version
- **AND** SHALL verify core_compatibility with current CLI version

#### Scenario: Install module already installed

- **WHEN** user installs module that is already installed
- **THEN** system SHALL display message "Module already installed (version X)"
- **AND** SHALL suggest using upgrade command

### Requirement: Uninstall command removes marketplace modules

The system SHALL provide `specfact module uninstall <module-name>` command that removes modules from marketplace path.

#### Scenario: Uninstall marketplace module

- **WHEN** user runs `specfact module uninstall backlog`
- **THEN** system SHALL check if module is from marketplace
- **AND** SHALL remove ~/.specfact/marketplace-modules/backlog/ directory
- **AND** SHALL remove module from registry
- **AND** SHALL display success message

#### Scenario: Attempt to uninstall built-in module

- **WHEN** user attempts to uninstall built-in module
- **THEN** system SHALL display error "Cannot uninstall built-in module"
- **AND** SHALL NOT modify module

### Requirement: Search command finds modules in registry

The system SHALL provide `specfact module search <query>` command that searches registry index by name, description, or tags.

#### Scenario: Search modules by keyword

- **WHEN** user runs `specfact module search backlog`
- **THEN** system SHALL fetch registry index
- **AND** SHALL filter modules matching query in name, description, or tags
- **AND** SHALL display results with module ID, description, latest version

### Requirement: List command shows installed modules

The system SHALL provide `specfact module list` command that displays modules from all sources with source indicators.

#### Scenario: List all modules

- **WHEN** user runs `specfact module list`
- **THEN** system SHALL show modules from built-in, marketplace, and custom paths
- **AND** SHALL indicate source (built-in/marketplace/custom) for each module

#### Scenario: List marketplace modules only

- **WHEN** user runs `specfact module list --source marketplace`
- **THEN** system SHALL show only marketplace-installed modules

### Requirement: Upgrade command updates installed modules

The system SHALL provide `specfact module upgrade [module-names...]` command that upgrades one or
more marketplace modules to their latest version. The command SHALL accept zero or more positional
module name arguments: no arguments upgrades all marketplace modules; one or more names restricts
the upgrade to only the named modules.

The upgrade output SHALL distinguish between modules that were actually upgraded to a new version
and modules that were already at the latest version. Showing `0.41.16 -> 0.41.16` when no version
change occurred is incorrect and SHALL NOT happen.

While the registry index is being fetched or a module is being installed, the CLI SHALL show visible
progress (for example a Rich status spinner) so the user knows work is ongoing. Rich progress MAY
be suppressed in automated test environments.

Before upgrading any module where the latest registry version has a higher major version than the
installed version, the CLI SHALL warn the user and require confirmation, because major version
bumps may contain breaking changes.

#### Scenario: Upgrade shows progress during registry fetch and install

- **WHEN** user runs `specfact module upgrade` and the registry fetch or an install takes noticeable time
- **THEN** the CLI SHALL show visible progress during fetch and during each module install

#### Scenario: Upgrade warns when registry index is unavailable

- **WHEN** the registry index cannot be fetched (offline or network error)
- **THEN** the CLI SHALL print a clear warning that the registry is unavailable
- **AND** SHALL continue using installed metadata where possible for the upgrade decision

#### Scenario: Upgrade a single named module to a newer minor/patch version

- **WHEN** user runs `specfact module upgrade backlog` and `0.42.0` is available (current `0.41.16`)
- **THEN** system SHALL fetch registry index
- **AND** SHALL confirm a newer version exists
- **AND** SHALL install the newer version without prompting (minor/patch, not a major bump)
- **AND** SHALL output `backlog: 0.41.16 -> 0.42.0`

#### Scenario: Upgrade multiple named modules selectively

- **WHEN** user runs `specfact module upgrade backlog codebase`
- **THEN** system SHALL upgrade only `backlog` and `codebase`
- **AND** SHALL NOT upgrade any other installed modules
- **AND** SHALL report each module's result independently

#### Scenario: Upgrade when module is already at latest version

- **WHEN** user runs `specfact module upgrade backlog` and no newer version is available
- **THEN** system SHALL NOT reinstall the module
- **AND** SHALL output `backlog: already up to date (0.41.16)` or equivalent
- **AND** SHALL NOT output `backlog: 0.41.16 -> 0.41.16`

#### Scenario: Upgrade all modules — mixed result (some upgraded, some current)

- **WHEN** user runs `specfact module upgrade` with no arguments (all modules)
- **AND** some modules have newer versions and some do not
- **THEN** the output SHALL have two sections:
  - `Upgraded:` listing only modules where the version actually changed
  - `Already up to date:` listing modules that were already at the latest version
- **AND** if no modules were upgraded, the output SHALL say "All modules are up to date"
  and SHALL NOT show any `X -> X` lines

#### Scenario: Upgrade detects a breaking major version bump and prompts

- **GIVEN** module `backlog` is installed at version `0.41.16`
- **AND** the registry offers version `1.0.0` as the latest
- **WHEN** user runs `specfact module upgrade backlog` in an interactive terminal
- **THEN** the CLI SHALL print a warning:
  `backlog: 0.41.16 -> 1.0.0 is a MAJOR version upgrade and may contain breaking changes.`
- **AND** SHALL prompt: `Upgrade anyway? [y/N]`
- **AND** SHALL only proceed if the user confirms with `y` or `Y`
- **AND** if the user declines, SHALL skip that module and continue with remaining targets

#### Scenario: Breaking major version upgrade bypassed with --yes flag

- **GIVEN** module `backlog` has a major version bump available
- **WHEN** user runs `specfact module upgrade backlog --yes`
- **THEN** the CLI SHALL upgrade without prompting
- **AND** SHALL print the warning line but not the confirmation prompt

#### Scenario: Breaking major version upgrade skipped silently in CI/CD mode

- **GIVEN** the CLI is running in CI/CD (non-interactive) mode
- **AND** a module has a major version bump available
- **WHEN** user runs `specfact module upgrade` without `--yes`
- **THEN** the CLI SHALL skip the module with a warning:
  `backlog: skipped — major version bump (0.41.16 -> 1.0.0). Re-run with --yes to upgrade.`
- **AND** SHALL exit 0 if all non-skipped modules succeeded

#### Scenario: Upgrade reinstalls when newer version is available

- **WHEN** a newer non-breaking version is available and the module is already installed
- **THEN** system SHALL replace existing installed files with the upgraded package
- **AND** SHALL NOT no-op due to existing install marker files

### Requirement: Installation extraction is path-safe

The system SHALL reject archive members that escape the intended extraction root.

#### Scenario: Installer blocks path traversal entries

- **WHEN** a downloaded marketplace tarball contains absolute paths or `..` traversal
- **THEN** install SHALL fail before extraction
- **AND** SHALL raise a validation error indicating unsafe archive content

### Requirement: Installation resolves pip dependencies before proceeding

The system SHALL extend install command to resolve pip dependencies across all modules before installation.

#### Scenario: Install with dependency resolution

- **WHEN** user installs module with pip_dependencies
- **THEN** system SHALL resolve dependencies with existing modules
- **AND** SHALL fail if conflicts detected
- **AND** SHALL install resolved dependencies if resolution succeeds

#### Scenario: Force install bypasses dependency resolution

- **WHEN** user runs install with --force flag
- **THEN** system SHALL skip dependency resolution
- **AND** SHALL log warning about potential conflicts
- **AND** SHALL proceed with installation

### Requirement: Install command accepts multiple module IDs in one invocation

The system SHALL allow `specfact module install` to accept one or more module IDs as positional
arguments so users can install several modules in a single command, consistent with the UX of
standard package managers (apt, pip, brew, npm).

#### Scenario: User installs multiple modules at once

- **WHEN** user runs `specfact module install nold-ai/specfact-codebase nold-ai/specfact-code-review`
- **THEN** the system SHALL install all listed modules in sequence
- **AND** SHALL print an install confirmation line for each module
- **AND** SHALL stop and report failure if any module install fails, leaving already-installed
  modules in place

#### Scenario: User installs a single module (existing behaviour unchanged)

- **WHEN** user runs `specfact module install nold-ai/specfact-codebase`
- **THEN** the system SHALL install the module exactly as before
- **AND** existing flags (`--scope`, `--source`, `--reinstall`, `--force`, `--skip-deps`) SHALL
  apply to all modules in the invocation

#### Scenario: Multi-install with one already-satisfied module

- **WHEN** user runs `specfact module install A B` and A is already installed
- **THEN** the system SHALL skip A with the existing "already installed" message
- **AND** SHALL still install B
- **AND** SHALL exit 0 if all non-skipped installs succeed

### Requirement: Uninstall command accepts multiple module names in one invocation

The system SHALL allow `specfact module uninstall` to accept one or more module names as positional
arguments so users can remove several modules in a single command, consistent with the multi-install
behaviour and the UX of standard package managers.

#### Scenario: User uninstalls multiple modules at once

- **WHEN** user runs `specfact module uninstall nold-ai/specfact-codebase nold-ai/specfact-code-review`
- **THEN** the system SHALL uninstall all listed modules in sequence
- **AND** SHALL print an uninstall confirmation line for each module
- **AND** SHALL continue with remaining modules if one fails, then exit non-zero

#### Scenario: User uninstalls a single module (existing behaviour unchanged)

- **WHEN** user runs `specfact module uninstall nold-ai/specfact-codebase`
- **THEN** the system SHALL uninstall the module exactly as before
- **AND** existing flags (`--scope`, `--repo`) SHALL apply to all modules in the invocation

#### Scenario: Multi-uninstall with one module not installed

- **WHEN** user runs `specfact module uninstall A B` and A is not installed
- **THEN** the system SHALL report that A is not found
- **AND** SHALL still attempt to uninstall B
- **AND** SHALL exit non-zero if any module failed or was not found

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

### Requirement: Module install enforces versioned bundle dependencies

The system SHALL validate versioned bundle dependency declarations during module installation.

#### Scenario: Existing dependency version is too old

- **GIVEN** a module being installed declares a bundle dependency with a version range
- **AND** that dependency already exists in the target install root with a version outside the range
- **WHEN** the user installs the dependent module
- **THEN** install fails before accepting the dependency set
- **AND** the error identifies the dependency id, required version range, and installed version

#### Scenario: Newly installed dependency version is validated

- **GIVEN** a module being installed declares a missing bundle dependency with a version range
- **WHEN** dependency installation completes
- **THEN** the installed dependency version is validated against the declared range
- **AND** install fails if the installed dependency still does not satisfy the range

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
