## MODIFIED Requirements

### Requirement: Upgrade command updates installed modules

The system SHALL provide `specfact module upgrade [module-names...]` command that upgrades one or
more marketplace modules to their latest version. The command SHALL accept zero or more positional
module name arguments: no arguments upgrades all marketplace modules; one or more names restricts
the upgrade to only the named modules.

The upgrade output SHALL distinguish between modules that were actually upgraded to a new version
and modules that were already at the latest version. Showing `0.41.16 -> 0.41.16` when no version
change occurred is incorrect and SHALL NOT happen.

Before upgrading any module where the latest registry version has a higher major version than the
installed version, the CLI SHALL warn the user and require confirmation, because major version
bumps may contain breaking changes.

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

## ADDED Requirements

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
