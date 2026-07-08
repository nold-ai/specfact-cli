# first-run-selection Specification

## Purpose

TBD - created by archiving change module-migration-01-categorize-and-group. Update Purpose after archive.

## Requirements

### Requirement: `specfact init` detects first-run and presents bundle selection

On a fresh install where no bundles are installed, `specfact init` SHALL present an interactive
bundle selection UI. When `--profile` is provided, `specfact init` SHALL install the profile's
canonical bundle set without requiring user interaction, and SHALL exit successfully only after
the bundles are fully installed and registered — not merely after runtime bootstrap.

#### Scenario: First-run interactive bundle selection in Copilot mode

- **GIVEN** a fresh SpecFact install with no bundles installed
- **AND** the CLI is running in Copilot (interactive) mode
- **WHEN** the user runs `specfact init`
- **THEN** the CLI SHALL display a welcome banner
- **AND** SHALL show the core modules as always-selected (non-deselectable): init, auth, module, upgrade
- **AND** SHALL present a multi-select list of the 5 workflow bundles with descriptions:
  - Project lifecycle (project, plan, import, sync, migrate)
  - Backlog management (backlog, policy)
  - Codebase quality (analyze, drift, validate, repro)
  - Spec & API (contract, spec, sdd, generate)
  - Governance (enforce, patch)
- **AND** SHALL offer profile preset shortcuts: Solo developer, Backlog team, API-first team, Enterprise full-stack
- **AND** SHALL install the user-selected bundles before completing workspace initialisation

#### Scenario: `init --profile` installs all profile bundles before completion

- **GIVEN** a fresh SpecFact install with no bundles installed
- **WHEN** the user runs `specfact init --profile solo-developer`
- **THEN** the CLI SHALL invoke the module installer for each bundle in the profile's canonical set
- **AND** SHALL NOT report "Bootstrap complete" until all profile bundles are installed and their
  commands are available in the CLI surface
- **AND** after the command completes, running `specfact code review run --help` SHALL succeed
  without a "Command not installed" error

#### Scenario: `init --profile` via uvx installs modules at user level

- **GIVEN** the user is running via `uvx specfact-cli`
- **WHEN** they run `uvx specfact-cli init --profile solo-developer`
- **THEN** the CLI SHALL install profile bundles to the user-level module root
  (e.g. `~/.specfact/modules/`) without requiring pip to be available in the uvx environment
- **AND** subsequent `uvx specfact-cli` invocations SHALL detect and load the installed modules

#### Scenario: User selects a profile preset during first-run

- **GIVEN** the first-run interactive UI is displayed
- **WHEN** the user selects "Enterprise full-stack" profile preset
- **THEN** the CLI SHALL auto-select bundles: project, backlog, codebase, spec, govern
- **AND** SHALL confirm the selection with a summary before installing
- **AND** SHALL install all five bundles via the module installer

#### Scenario: User skips bundle selection during first-run

- **GIVEN** the first-run interactive UI is displayed
- **WHEN** the user selects no bundles and confirms
- **THEN** the CLI SHALL install only core modules
- **AND** SHALL display a tip: "Install bundles later with `specfact module install <bundle>`"
- **AND** SHALL complete workspace initialisation with only core commands available

### Requirement: `specfact init --profile <name>` installs a named preset non-interactively

The system SHALL accept a `--profile <name>` argument on `specfact init` and MUST install the canonical bundle set for that profile without prompting, whether in CI/CD mode or interactive mode.

#### Scenario: `--profile` installs preset bundles without interaction

- **GIVEN** the CLI is in CI/CD mode OR the user passes `--profile`
- **WHEN** the user runs `specfact init --profile solo-developer`
- **THEN** the CLI SHALL install bundle `specfact-codebase` without prompting
- **AND** SHALL print a summary of installed bundles to stdout
- **AND** SHALL exit 0

#### Scenario: Profile presets map to canonical bundle sets

- **GIVEN** a valid `--profile` value
- **WHEN** `specfact init` processes the profile
- **THEN** the bundle set installed SHALL match exactly:
  - `solo-developer` → `specfact-codebase`
  - `backlog-team` → `specfact-backlog`, `specfact-project`, `specfact-codebase`
  - `api-first-team` → `specfact-spec`, `specfact-codebase`
  - `enterprise-full-stack` → `specfact-project`, `specfact-backlog`, `specfact-codebase`, `specfact-spec`, `specfact-govern`

#### Scenario: Invalid `--profile` value produces actionable error

- **GIVEN** the user runs `specfact init --profile nonexistent`
- **WHEN** `specfact init` processes the argument
- **THEN** the CLI SHALL print an error listing valid profile names
- **AND** SHALL exit with a non-zero exit code

### Requirement: `specfact init --install <bundles>` installs an explicit bundle list

The system SHALL accept a `--install <bundle-list>` argument on `specfact init` and MUST install the named bundles without prompting. The value `all` SHALL install every available category bundle.

#### Scenario: `--install` installs comma-separated bundle list

- **GIVEN** the user runs `specfact init --install backlog,codebase`
- **WHEN** `specfact init` processes the argument
- **THEN** the CLI SHALL install `specfact-backlog` and `specfact-codebase`
- **AND** SHALL NOT prompt for any interactive selection
- **AND** SHALL exit 0

#### Scenario: `--install all` installs every available bundle

- **GIVEN** the user runs `specfact init --install all`
- **WHEN** `specfact init` processes the argument
- **THEN** the CLI SHALL install all current workflow bundles: project, backlog, codebase, spec, govern, requirements
- **AND** SHALL exit 0

#### Scenario: `--install` with unknown bundle name fails gracefully

- **GIVEN** the user runs `specfact init --install widgets`
- **WHEN** `specfact init` processes the argument
- **THEN** the CLI SHALL print an error identifying the unknown bundle name
- **AND** SHALL list valid bundle names
- **AND** SHALL exit with a non-zero exit code

### Requirement: Bundle installation during init uses existing module installer

The `specfact init` command SHALL delegate all bundle installation to the existing `module_installer.install_module()` function and MUST resolve bundle-level dependencies via the marketplace-02 dependency resolver before installing any bundle.

#### Scenario: Init delegates bundle installation to module installer

- **GIVEN** `specfact init --profile backlog-team` is invoked
- **WHEN** the init command processes bundle installation
- **THEN** it SHALL call the existing `module_installer.install_module()` for each bundle
- **AND** SHALL handle installer errors (network failure, signature mismatch) and surface them clearly
- **AND** SHALL NOT partially install bundles (all-or-nothing per bundle)

#### Scenario: Bundle install during init resolves bundle-level dependencies

- **GIVEN** the user selects the `spec` bundle (which depends on `project` bundle)
- **WHEN** init processes the selection
- **THEN** the module installer SHALL automatically include `specfact-project` as a dependency
- **AND** SHALL inform the user: "Installing specfact-project as required dependency of specfact-spec"
