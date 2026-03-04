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

Bootstrap SHALL mount only category group apps (and core commands) when `category_grouping_enabled` is true. It SHALL NOT register any shim loaders for flat command names.

#### Scenario: No shim registration at bootstrap

- **GIVEN** `category_grouping_enabled` is `true`
- **WHEN** the CLI bootstrap runs
- **THEN** the registry SHALL contain entries only for core commands and the five category group names
- **AND** SHALL NOT contain entries for `analyze`, `drift`, `validate`, `repro`, `backlog`, `policy`, `project`, `plan`, `import`, `sync`, `migrate`, `contract`, `spec`, `sdd`, `generate`, `enforce`, `patch` as top-level commands

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

