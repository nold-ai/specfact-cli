# profile-presets Specification

## Purpose

Defines the fully-activated profile preset behaviour for `specfact init` after core slimming. With the bundled fallback removed, `specfact init` must now enforce that at least one bundle is installed before workspace initialisation completes. This spec covers the mandatory first-run bundle selection gate, the complete profile-to-bundle mapping, the CI/CD non-interactive path, and the first-use guard that prevents workspace use before bundle selection.

This spec builds on the `first-run-selection` spec from module-migration-01. That spec introduced the UI and `--profile` / `--install` flags. This spec adds enforcement (the selection is now mandatory, not optional) and the first-use guard, which are only meaningful after core slimming removes the bundled fallback.

## ADDED Requirements

### Requirement: `specfact init` enforces bundle selection on a fresh install

On a fresh install with no bundles installed, `specfact init` SHALL NOT complete workspace initialisation until the user has selected and installed at least one bundle (or the user explicitly confirms the core-only install).

#### Scenario: First-run init blocks until bundle selection is confirmed

- **GIVEN** a fresh specfact-cli install with no bundles installed
- **AND** the CLI is running in Copilot (interactive) mode
- **WHEN** the user runs `specfact init` without `--profile` or `--install`
- **THEN** the CLI SHALL display the welcome banner and bundle selection UI (as defined by `first-run-selection` spec)
- **AND** SHALL NOT proceed to workspace directory setup until the user makes a selection
- **AND** if the user selects no bundles and attempts to confirm, the CLI SHALL prompt: "You haven't selected any bundles. Install at least one bundle for workflow commands, or press Enter to continue with core only."
- **AND** SHALL complete if the user explicitly confirms core-only (with a tip to install bundles later)

#### Scenario: First-run init in CI/CD mode requires --profile or --install

- **GIVEN** a fresh specfact-cli install with no bundles installed
- **AND** the CLI detects CI/CD mode (non-interactive environment)
- **WHEN** the user runs `specfact init` without `--profile` or `--install`
- **THEN** the CLI SHALL print an error: "In CI/CD mode, --profile or --install is required. Example: specfact init --profile solo-developer"
- **AND** SHALL exit with a non-zero exit code
- **AND** SHALL NOT attempt interactive bundle selection

#### Scenario: Subsequent `specfact init` runs do not enforce bundle selection again

- **GIVEN** `specfact init` has been run previously and at least one bundle is installed
- **WHEN** the user runs `specfact init` again (workspace re-initialisation)
- **THEN** the CLI SHALL NOT show the bundle selection gate
- **AND** SHALL run the standard workspace re-initialisation flow
- **AND** SHALL show the currently installed bundles as informational output

### Requirement: Profile presets are fully activated and install bundles from the marketplace

The four profile presets SHALL resolve to the exact canonical bundle set and install each bundle via the marketplace installer. Profiles are now the primary onboarding path.

#### Scenario: solo-developer profile installs specfact-codebase

- **GIVEN** a fresh specfact-cli install
- **WHEN** the user runs `specfact init --profile solo-developer`
- **THEN** the CLI SHALL install `specfact-codebase` from the marketplace registry (no interaction required)
- **AND** SHALL confirm: "Installed: specfact-codebase (codebase quality bundle)"
- **AND** SHALL exit 0
- **AND** `specfact code --help` SHALL resolve after init completes

#### Scenario: backlog-team profile installs three bundles in dependency order

- **GIVEN** a fresh specfact-cli install
- **WHEN** the user runs `specfact init --profile backlog-team`
- **THEN** the CLI SHALL install: `specfact-project`, `specfact-backlog`, `specfact-codebase`
- **AND** SHALL install `specfact-project` before `specfact-backlog` (no explicit cross-bundle dependency, but installation order matches the canonical profile definition)
- **AND** SHALL confirm each installed bundle
- **AND** SHALL exit 0

#### Scenario: api-first-team profile installs spec and codebase bundles (with project as transitive dep)

- **GIVEN** a fresh specfact-cli install
- **WHEN** the user runs `specfact init --profile api-first-team`
- **THEN** the CLI SHALL install: `specfact-spec`, `specfact-codebase`
- **AND** `specfact-project` SHALL be auto-installed as a bundle-level dependency of `specfact-spec`
- **AND** the CLI SHALL inform: "Installing specfact-project as required dependency of specfact-spec"
- **AND** SHALL exit 0

#### Scenario: enterprise-full-stack profile installs all five bundles

- **GIVEN** a fresh specfact-cli install
- **WHEN** the user runs `specfact init --profile enterprise-full-stack`
- **THEN** the CLI SHALL install all five bundles: `specfact-project`, `specfact-backlog`, `specfact-codebase`, `specfact-spec`, `specfact-govern`
- **AND** `specfact-project` SHALL be installed before `specfact-spec` and `specfact-govern` (dependency order)
- **AND** SHALL exit 0
- **AND** `specfact --help` SHALL show all 9 top-level commands (4 core + 5 category groups)

#### Scenario: Profile preset map is exhaustive and canonical

- **GIVEN** a request for any valid profile name
- **WHEN** `specfact init --profile <name>` is executed
- **THEN** the installed bundle set SHALL match exactly:
  - `solo-developer` → `[specfact-codebase]`
  - `backlog-team` → `[specfact-project, specfact-backlog, specfact-codebase]`
  - `api-first-team` → `[specfact-spec, specfact-codebase]` (specfact-project auto-installed as dep)
  - `enterprise-full-stack` → `[specfact-project, specfact-backlog, specfact-codebase, specfact-spec, specfact-govern]`
- **AND** no profile SHALL install bundles outside its canonical set

#### Scenario: Invalid profile name produces actionable error

- **GIVEN** the user runs `specfact init --profile unknown-profile`
- **WHEN** `specfact init` processes the argument
- **THEN** the CLI SHALL print an error listing valid profile names: solo-developer, backlog-team, api-first-team, enterprise-full-stack
- **AND** SHALL exit with a non-zero exit code (1)

### Requirement: First-use guard prevents non-core command execution before any bundle is installed

If the user attempts to run a category group command (e.g., `specfact project`, `specfact backlog`) without the corresponding bundle installed, the CLI SHALL provide an actionable error pointing to `specfact init` or `specfact module install`.

#### Scenario: Non-core category command without bundle installed produces helpful error

- **GIVEN** no bundles are installed
- **WHEN** the user runs `specfact backlog ceremony standup`
- **THEN** the CLI SHALL print: "The 'backlog' bundle is not installed. Run: specfact init --profile backlog-team  OR  specfact module install nold-ai/specfact-backlog"
- **AND** SHALL exit with a non-zero exit code
- **AND** SHALL NOT produce a stack trace or internal exception message

#### Scenario: Core commands always work regardless of bundle installation state

- **GIVEN** no bundles are installed
- **WHEN** the user runs any core command: `specfact init`, `specfact auth`, `specfact module`, `specfact upgrade`
- **THEN** the command SHALL execute normally
- **AND** SHALL NOT be gated by bundle installation state

### Requirement: `specfact init --install all` still installs all five bundles

The `--install all` shorthand, introduced by `first-run-selection` (module-migration-01), SHALL continue to work after core slimming.

#### Scenario: --install all installs all five category bundles from marketplace

- **GIVEN** a fresh specfact-cli install
- **WHEN** the user runs `specfact init --install all`
- **THEN** the CLI SHALL install all five bundles from the marketplace registry: specfact-project, specfact-backlog, specfact-codebase, specfact-spec, specfact-govern
- **AND** SHALL resolve bundle dependencies (specfact-project installed before specfact-spec and specfact-govern)
- **AND** SHALL exit 0
- **AND** this behaviour SHALL be identical to the pre-slimming `--install all` behaviour that previously enabled all bundled modules

#### Scenario: CI/CD pipelines using --install all are not broken

- **GIVEN** an existing CI/CD pipeline that runs `specfact init --install all` as a bootstrap step
- **WHEN** the pipeline runs after the core slimming upgrade
- **THEN** all 21 commands SHALL be available after the init step completes
- **AND** the pipeline SHALL not require any changes to continue functioning

## MODIFIED Requirements

### Modified Requirement: first-run-selection bundle selection is now mandatory (not optional)

This is a delta to the `first-run-selection` spec from module-migration-01. In that spec, skipping bundle selection was allowed (user could complete init with no bundles). After core slimming, that path is gated.

#### Scenario: Skipping bundle selection in interactive mode produces a second prompt

- **GIVEN** the first-run bundle selection UI is displayed (interactive mode)
- **WHEN** the user selects no bundles and presses Enter to confirm
- **THEN** the CLI SHALL NOT silently accept the empty selection
- **AND** SHALL display a single confirmation prompt: "Continue with core only? (4 commands available; install bundles later with `specfact module install`). [y/N]:"
- **AND** if the user enters 'y', SHALL complete with core-only and show the install tip
- **AND** if the user enters 'n' or presses Enter (default No), SHALL return to the bundle selection UI
