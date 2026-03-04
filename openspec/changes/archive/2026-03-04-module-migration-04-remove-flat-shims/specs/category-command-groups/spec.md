# category-command-groups Specification (Delta: Remove Flat Shims)

## Purpose

This delta removes the backward-compat shim layer for flat commands. After this change, the root CLI SHALL list only core commands and the five category groups when `category_grouping_enabled` is true.

## REMOVED Requirements

### Requirement: Backward-compat shims preserve all existing flat top-level commands

*(Removed in 0.40.x. Flat commands are no longer registered; users MUST use category form.)*

#### Scenario: Root help lists only core and category groups

- **GIVEN** `category_grouping_enabled` is `true`
- **WHEN** the user runs `specfact --help`
- **THEN** the output SHALL list only: core commands (`init`, `auth`, `module`, `upgrade`) and the five category groups (`code`, `backlog`, `project`, `spec`, `govern`)
- **AND** SHALL NOT list any of the 17 former flat shim commands (e.g. `analyze`, `validate`, `plan`, `sync`)

#### Scenario: Flat command name returns error

- **GIVEN** `category_grouping_enabled` is `true`
- **WHEN** the user runs `specfact validate --help`
- **THEN** the CLI SHALL respond with an error indicating the command is not found
- **AND** SHALL suggest using `specfact code validate` or list available commands

## MODIFIED Requirements

### Requirement: Bootstrap mounts category groups when grouping is enabled

Bootstrap SHALL mount only category group apps (and core commands) when `category_grouping_enabled` is true. It SHALL NOT register any shim loaders for flat command names.

#### Scenario: No shim registration at bootstrap

- **GIVEN** `category_grouping_enabled` is `true`
- **WHEN** the CLI bootstrap runs
- **THEN** the registry SHALL contain entries only for core commands and the five category group names
- **AND** SHALL NOT contain entries for `analyze`, `drift`, `validate`, `repro`, `backlog`, `policy`, `project`, `plan`, `import`, `sync`, `migrate`, `contract`, `spec`, `sdd`, `generate`, `enforce`, `patch` as top-level commands
