## MODIFIED Requirements

### Requirement: Root command diagnostics respect the canonical command surface

The CLI SHALL render module installation, disabled, skipped, or shadowed diagnostics only for canonical root command groups that are still part of the supported command surface.

#### Scenario: Removed flat aliases are not treated as missing marketplace modules

- **GIVEN** flat root aliases such as `validate`, `plan`, `analyze`, `drift`, `repro`, `sync`, and `migrate` are not registered as supported root CLI commands
- **WHEN** a user invokes one of those removed flat aliases
- **THEN** the CLI SHALL NOT classify the command through marketplace module availability
- **AND** the CLI SHALL NOT report that a providing module is absent, disabled, skipped, or shadowed
- **AND** the CLI SHALL report the command path as removed or unknown with guidance to the canonical grouped command when a canonical replacement exists

#### Scenario: Canonical grouped commands retain actionable module diagnostics

- **GIVEN** a canonical root command group such as `code` or `project` is not registered because its providing module is absent, disabled, skipped, or incompatible
- **WHEN** the user invokes that canonical group
- **THEN** the CLI SHALL continue to render actionable module diagnostics for the providing marketplace module

#### Scenario: Project-scoped modules do not make removed aliases look shadowed

- **GIVEN** a workspace has both user-scope and project-scope copies of the same marketplace module installed
- **AND** the project-scope copy is the effective active module
- **WHEN** a user invokes a removed flat alias formerly provided by that module
- **THEN** the CLI SHALL NOT report that the module is shadowed
- **AND** the CLI SHALL direct the user to the canonical grouped command path or report the alias as removed
