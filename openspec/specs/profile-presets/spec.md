# profile-presets Specification

## Purpose

TBD - created by archiving change module-migration-03-core-slimming. Update Purpose after archive.

## Requirements

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

The four profile presets SHALL resolve to the exact canonical bundle set and install each bundle
via the marketplace installer. The `solo-developer` profile SHALL include
`nold-ai/specfact-code-review` so that `specfact code review run` is available immediately after
running `specfact init --profile solo-developer`.

#### Scenario: solo-developer profile installs codebase and code-review bundles

- **GIVEN** a fresh SpecFact install or an install where specfact-codebase and specfact-code-review
  are not yet installed
- **WHEN** the user runs `specfact init --profile solo-developer`
- **THEN** the CLI SHALL install `nold-ai/specfact-codebase` from the marketplace registry
- **AND** SHALL install `nold-ai/specfact-code-review` from the marketplace registry
- **AND** SHALL confirm: "Installed: specfact-codebase, specfact-code-review"
- **AND** after completion, `specfact code review run --path . --scope full` SHALL be available
  and produce a scored review result

#### Scenario: backlog-team profile installs three bundles in dependency order

- **GIVEN** a fresh SpecFact install
- **WHEN** the user runs `specfact init --profile backlog-team`
- **THEN** the CLI SHALL install: `specfact-project`, `specfact-backlog`, `specfact-codebase`
- **AND** SHALL install `specfact-project` before `specfact-backlog`

#### Scenario: api-first-team profile installs spec and codebase bundles

- **GIVEN** a fresh SpecFact install
- **WHEN** the user runs `specfact init --profile api-first-team`
- **THEN** the CLI SHALL install: `specfact-spec`, `specfact-codebase`
- **AND** `specfact-project` SHALL be auto-installed if required as a transitive dependency

#### Scenario: enterprise-full-stack profile installs all five bundles

- **GIVEN** a fresh SpecFact install
- **WHEN** the user runs `specfact init --profile enterprise-full-stack`
- **THEN** the CLI SHALL install all five bundles:
  `specfact-project`, `specfact-backlog`, `specfact-codebase`, `specfact-spec`, `specfact-govern`

#### Scenario: Profile canonical bundle mapping is machine-verifiable

- **GIVEN** a request for any valid profile name
- **WHEN** `specfact init --profile <name>` is executed
- **THEN** the resolved bundle set SHALL be:
  - `solo-developer` → `[specfact-codebase, specfact-code-review]`
  - `backlog-team` → `[specfact-project, specfact-backlog, specfact-codebase]`
  - `api-first-team` → `[specfact-spec, specfact-codebase]`
  - `enterprise-full-stack` → `[specfact-project, specfact-backlog, specfact-codebase, specfact-spec, specfact-govern]`
- **AND** no profile SHALL install bundles outside its canonical set

#### Scenario: Invalid profile name produces actionable error

- **GIVEN** the user runs `specfact init --profile unknown-profile`
- **WHEN** the CLI processes the command
- **THEN** the CLI SHALL print an error listing valid profile names:
  solo-developer, backlog-team, api-first-team, enterprise-full-stack

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
- **WHEN** the user runs any core command: `specfact init`, `specfact module`, `specfact upgrade`
- **THEN** the command SHALL execute normally
- **AND** SHALL NOT be gated by bundle installation state
- **AND** auth commands SHALL be available via `specfact backlog auth` once the backlog bundle is installed

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
