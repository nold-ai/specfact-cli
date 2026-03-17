## ADDED Requirements

### Requirement: Code Review Module Registration
The `nold-ai/specfact-code-review` module SHALL be installable and extend `specfact code` with a `review` subgroup exposing `run`, `ledger`, and `rules` subcommands.

#### Scenario: Module install surfaces review subgroup
- **GIVEN** the module is installed via `specfact module install nold-ai/specfact-code-review`
- **WHEN** the user runs `specfact code --help`
- **THEN** a `review` subgroup appears in the command list
- **AND** `specfact code review --help` shows `run`, `ledger`, and `rules` subcommands

#### Scenario: module-package.yaml has required fields
- **GIVEN** `packages/specfact-code-review/module-package.yaml` exists
- **WHEN** the module loader parses it
- **THEN** `bundle_group_command` equals `code`, `tier` equals `official`, `name` equals `nold-ai/specfact-code-review`
- **AND** `core_compatibility` matches `>=0.40.0,<1.0.0`

#### Scenario: Module not installed produces no surface
- **GIVEN** the module is NOT installed
- **WHEN** the user runs `specfact code --help`
- **THEN** no `review` subgroup appears and no error is raised

#### Scenario: Duplicate install is idempotent
- **GIVEN** the module is already installed
- **WHEN** the user installs it again
- **THEN** no duplicate `review` entries appear in `specfact code --help`
