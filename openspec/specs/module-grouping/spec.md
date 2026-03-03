# module-grouping Specification

## Purpose
TBD - created by archiving change module-migration-01-categorize-and-group. Update Purpose after archive.
## Requirements
### Requirement: Module-package.yaml declares category metadata

Every `module-package.yaml` file SHALL declare four new fields: `category`, `bundle`, `bundle_group_command`, and `bundle_sub_command`.

#### Scenario: Core module declares core category

- **GIVEN** a module that is permanently part of the specfact-cli core (init, auth, module_registry, upgrade)
- **WHEN** the registry reads its `module-package.yaml`
- **THEN** the manifest SHALL contain `category: core`
- **AND** SHALL NOT contain `bundle` or `bundle_group_command` (core modules are never grouped under a category command)
- **AND** SHALL contain `bundle_sub_command` equal to the module's existing top-level command name

#### Scenario: Non-core module declares category and bundle

- **GIVEN** a non-core module (any of the 17 non-core modules)
- **WHEN** the registry reads its `module-package.yaml`
- **THEN** the manifest SHALL contain a `category` matching one of: `project`, `backlog`, `codebase`, `spec`, `govern`
- **AND** SHALL contain a `bundle` matching the canonical bundle name for that category (e.g., `specfact-codebase`)
- **AND** SHALL contain a `bundle_group_command` equal to the top-level group command for that category (e.g., `code`)
- **AND** SHALL contain a `bundle_sub_command` equal to the sub-command name within the group

#### Scenario: Category assignment follows canonical mapping

- **GIVEN** the canonical category table from the implementation plan
- **WHEN** any module-package.yaml is read
- **THEN** the `category` and `bundle` values SHALL match the canonical assignment exactly:
  - `project` category → bundle `specfact-project` → modules: project, plan, import_cmd, sync, migrate → group command `project`
  - `backlog` category → bundle `specfact-backlog` → modules: backlog, policy_engine → group command `backlog`
  - `codebase` category → bundle `specfact-codebase` → modules: analyze, drift, validate, repro → group command `code`
  - `spec` category → bundle `specfact-spec` → modules: contract, spec, sdd, generate → group command `spec`
  - `govern` category → bundle `specfact-govern` → modules: enforce, patch_mode → group command `govern`

### Requirement: Registry groups modules by category when loading

The registry SHALL read `category` and `bundle_group_command` from each module manifest and group modules accordingly.

#### Scenario: Registry collects category groups from installed modules

- **GIVEN** `category_grouping_enabled` is `true` (default)
- **WHEN** the registry initialises and scans installed modules
- **THEN** it SHALL produce a `dict[str, list[ModulePackage]]` mapping each `bundle_group_command` to its member modules
- **AND** SHALL treat `core` category modules as ungrouped top-level commands

#### Scenario: Registry falls back to flat mounting when grouping disabled

- **GIVEN** `category_grouping_enabled` is `false`
- **WHEN** the registry initialises
- **THEN** it SHALL mount each module as a flat top-level command
- **AND** SHALL NOT create any category group commands
- **AND** SHALL log a debug message indicating flat mode is active

#### Scenario: Module with missing category fields is handled gracefully

- **GIVEN** a module-package.yaml that does not contain the `category` field (legacy or external module)
- **WHEN** the registry reads the manifest
- **THEN** the registry SHALL treat the module as `category: core` (ungrouped)
- **AND** SHALL log a warning: "Module <name> has no category field; mounting as flat top-level command"
- **AND** SHALL NOT raise an exception or prevent startup

### Requirement: Category metadata fields are validated at module load time

The registry SHALL validate the four metadata fields on load and reject manifests that violate the schema.

#### Scenario: Invalid category value is rejected

- **GIVEN** a module-package.yaml with `category: unknown`
- **WHEN** the registry attempts to load the module
- **THEN** the registry SHALL raise a `ModuleManifestError` with message indicating the unknown category
- **AND** SHALL NOT mount the module

#### Scenario: Mismatched bundle_group_command is rejected

- **GIVEN** a module-package.yaml where `bundle_group_command` does not match the canonical command for its `category`
- **WHEN** the registry attempts to load the module
- **THEN** the registry SHALL raise a `ModuleManifestError`
- **AND** SHALL include the expected and actual values in the error message

