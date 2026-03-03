# category-command-groups Specification

## Purpose
TBD - created by archiving change module-migration-01-categorize-and-group. Update Purpose after archive.
## Requirements
### Requirement: Category group commands aggregate member module sub-apps

Each category group SHALL expose its member modules as sub-commands, preserving all existing sub-command names from each module.

#### Scenario: Category group exposes module sub-commands

- **GIVEN** `category_grouping_enabled` is `true`
- **AND** a category bundle (e.g., `specfact-codebase`) is installed
- **WHEN** the user runs `specfact code --help`
- **THEN** the output SHALL list sub-commands for each member module: `analyze`, `drift`, `validate`, `repro`
- **AND** each sub-command SHALL be the `bundle_sub_command` value from that module's manifest
- **AND** the help text SHALL describe the category group purpose

#### Scenario: Module sub-commands are accessible via category group

- **GIVEN** the `codebase` bundle is installed
- **WHEN** the user runs `specfact code analyze contracts`
- **THEN** the command SHALL execute identically to the original `specfact analyze contracts`
- **AND** the exit code, output format, and side effects SHALL be identical

#### Scenario: Grouped registration preserves command extensions for duplicate command names

- **GIVEN** `category_grouping_enabled` is `true`
- **AND** a base module provides command group `backlog`
- **AND** an extension module also declares command group `backlog`
- **WHEN** module package commands are registered
- **THEN** the registry SHALL merge extension subcommands into the existing `backlog` command tree
- **AND** SHALL NOT replace the existing loader with only the extension loader
- **AND** both base and extension subcommands SHALL remain accessible under `specfact backlog ...`

#### Scenario: Category group command is absent when bundle not installed

- **GIVEN** the `govern` bundle is NOT installed
- **WHEN** the user runs `specfact --help`
- **THEN** `govern` SHALL NOT appear in the help output
- **WHEN** the user runs `specfact govern --help`
- **THEN** the CLI SHALL display an error indicating the command is not found
- **AND** SHALL suggest `specfact module install specfact-govern`

### Requirement: Bootstrap mounts category groups when grouping is enabled

`bootstrap.py` SHALL mount category group apps on the root Typer instance when `category_grouping_enabled` is `true`.

#### Scenario: Bootstrap mounts all installed category groups

- **GIVEN** `category_grouping_enabled` is `true`
- **AND** modules from multiple categories are installed
- **WHEN** the CLI initialises
- **THEN** `bootstrap.py` SHALL call `app.add_typer()` for each category group app that has at least one member module installed
- **AND** SHALL NOT mount flat individual module apps for grouped modules
- **AND** SHALL still mount `core` category modules as flat top-level commands

#### Scenario: Category group lazy-loads member modules on first invocation

- **GIVEN** a category group is mounted
- **WHEN** the user runs a sub-command under the group
- **THEN** the group SHALL defer importing member module sub-apps until the sub-command is invoked
- **AND** the import SHALL succeed and the command SHALL execute
- **AND** CLI startup time (for `specfact --help`) SHALL NOT increase by more than 50ms compared to pre-grouping baseline

### Requirement: Backward-compat shims preserve all existing flat top-level commands

All 17 non-core module commands that existed before this change SHALL remain functional as flat top-level commands during the migration window, but SHALL emit a deprecation warning in interactive mode.

#### Scenario: Old flat command delegates to category group equivalent

- **GIVEN** `category_grouping_enabled` is `true`
- **AND** the `specfact validate` flat shim is active
- **WHEN** the user runs `specfact validate sidecar run` in interactive (Copilot) mode
- **THEN** the CLI SHALL print a yellow deprecation warning: "Note: `specfact validate` is deprecated. Use `specfact code validate` instead."
- **AND** SHALL delegate the command to `specfact code validate sidecar run`
- **AND** the command SHALL complete with the same exit code and output as the category group equivalent

#### Scenario: Old flat command runs silently in CI/CD mode

- **GIVEN** `category_grouping_enabled` is `true`
- **AND** the CLI is running in CICD mode (detected from environment or `--cicd` flag)
- **WHEN** the user runs `specfact plan init`
- **THEN** the CLI SHALL execute `specfact project plan init` silently
- **AND** SHALL NOT print any deprecation warning
- **AND** the exit code and output SHALL be identical to the category group equivalent

#### Scenario: All 17 non-core flat commands remain in help output during migration window

- **GIVEN** `category_grouping_enabled` is `true`
- **AND** the migration window is active (i.e., shims have not been removed)
- **WHEN** the user runs `specfact --help`
- **THEN** both the category group commands AND the flat shim commands SHALL appear in help
- **AND** shim entries SHALL include a deprecation annotation in their help text

### Requirement: `category_grouping_enabled` config flag controls grouping behaviour

The system SHALL read the `category_grouping_enabled` flag from user config at CLI startup and MUST use it to determine whether category group apps or flat module apps are mounted.

#### Scenario: Grouping enabled by default

- **GIVEN** no explicit `category_grouping_enabled` value in user config
- **WHEN** the CLI initialises
- **THEN** `category_grouping_enabled` SHALL default to `true`

#### Scenario: Grouping disabled via config

- **GIVEN** user config contains `category_grouping_enabled: false`
- **WHEN** the CLI initialises
- **THEN** all modules SHALL be mounted as flat top-level commands
- **AND** no category group commands SHALL appear in `specfact --help`
- **AND** no deprecation warnings SHALL be emitted for flat commands

### Requirement: spec module sub-command avoids collision with group command name

The system SHALL mount the `spec` module as the `api` sub-command within the `spec` category group to avoid a name collision between the module command and the group command. The flat shim MUST still delegate `specfact spec <sub>` to `specfact spec api <sub>` during the migration window.

The `spec` module's existing `specfact spec` command conflicts with the `specfact spec` category group command.

#### Scenario: spec module mounts as `api` sub-command within spec group

- **GIVEN** the `specfact-spec` bundle is installed
- **WHEN** the user runs `specfact spec --help`
- **THEN** the sub-command for the `spec` module SHALL appear as `api` (not `spec`)
- **AND** the `spec` module's `validate`, `backward-compat`, `generate-tests`, and `mock` sub-commands SHALL be accessible via `specfact spec api <sub-command>`
- **AND** the flat shim `specfact spec <sub-command>` SHALL still delegate to `specfact spec api <sub-command>` during the migration window

