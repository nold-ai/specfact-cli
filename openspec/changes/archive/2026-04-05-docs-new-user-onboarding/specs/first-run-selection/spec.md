## MODIFIED Requirements

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
