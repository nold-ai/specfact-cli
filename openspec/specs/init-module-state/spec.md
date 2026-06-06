# init-module-state Specification

## Purpose

TBD - created by archiving change arch-01-cli-modular-command-registry. Update Purpose after archive.
## Requirements
### Requirement: Init Discovers Modules and Stores State with Version and Enabled Flag

When the user runs **specfact init**, the CLI SHALL discover all available module packages, SHALL treat each as **enabled by default**, and SHALL write a **state file** under `~/.specfact/registry/` (e.g. `modules.json`) that records for each module: identifier, version, and **enabled** (boolean). Subsequent runs of specfact init SHALL read this state file and SHALL respect previously set enabled/disabled values (user overrides).

**Rationale**: Enables users to disable specific modules and have that choice persist; prepares for future selective install.

#### Scenario: First Init Writes State with All Modules Enabled

**Given**: User has not run specfact init before (or state file is missing)

**When**: User runs `specfact init`

**Then**: After existing init logic, discovery runs; state file is written with every discovered module and `enabled: true`; root help cache (commands.json) is updated as in help-cache spec

**Acceptance Criteria**:

- State file exists at ~/.specfact/registry/modules.json (or equivalent)
- Each discovered module appears with at least: id, version, enabled (true)
- All modules are enabled by default on first run

#### Scenario: Init Respects Manual Deselection on Next Run

**Given**: State file exists and module "backlog_daily" has `enabled: false` (set by user via CLI or manual edit)

**When**: User runs `specfact init` again (e.g. after upgrade or re-run)

**Then**: "backlog_daily" remains disabled; state file is updated (e.g. version refreshed) but enabled flag for "backlog_daily" stays false; user is informed that some modules are disabled by configuration

**Acceptance Criteria**:

- Reading state file restores enabled/disabled per module
- Only modules with enabled: true are registered (or exposed) for commands; disabled modules are not loaded
- New modules (not in state file) get enabled: true when first discovered

#### Scenario: CLI Options to Enable or Disable Modules

**Given**: User runs specfact init with options to change module state

**When**: User runs `specfact init --disable-module backlog_daily` or `specfact init --enable-module backlog_daily`

**Then**: The specified module's enabled flag is set to false or true; state file is written with the new value; on next init this value is preserved unless overridden again

**Acceptance Criteria**:

- --enable-module <id> and --disable-module <id> are supported (multiple allowed)
- State file is updated after init so overrides persist
- After init, if any module is disabled and that is due to user override (saved in state), print a message: e.g. "The following modules are disabled by your configuration: <list>. Re-enable with specfact init --enable-module <id>."

### Requirement: Init Profile State Refresh Is Repo-Aware and Merge-Based

When `specfact init` installs or refreshes modules, the system SHALL discover project-scope modules relative to the selected repository path and SHALL merge discovered module rows with existing lifecycle state instead of replacing unrelated state blindly.

#### Scenario: Init profile uses repo option for project discovery

- **GIVEN** the current working directory is outside `<repo>`
- **AND** `<repo>/.specfact/modules/<module-name>` exists
- **WHEN** the user runs `specfact init --repo <repo> --profile <profile>`
- **THEN** init SHALL use `<repo>` when discovering project-scope modules for state refresh and prompt audits
- **AND** init SHALL NOT use an unrelated current working directory as the project module root

#### Scenario: Init preserves disabled state for rediscovered modules

- **GIVEN** `modules.json` marks a discovered module as disabled
- **WHEN** the user runs `specfact init --profile <profile>`
- **THEN** init SHALL preserve that module's disabled state unless the user explicitly enables it
- **AND** init SHALL report actionable re-enable guidance when the disabled module belongs to the selected profile

#### Scenario: Init does not drop unrelated module state from another context

- **GIVEN** `modules.json` contains a module row that is not visible from the current repository discovery context
- **WHEN** the user runs `specfact init --repo <repo> --profile <profile>`
- **THEN** init SHALL NOT delete or reset that unrelated row solely because it is absent from the current discovery view
- **AND** discovered rows for the selected repository SHALL still have current version and enabled metadata

#### Scenario: Init profile install repairs installed-but-disabled profile module

- **GIVEN** a profile-selected module artifact already exists
- **AND** lifecycle state marks that module as disabled
- **WHEN** the user runs `specfact init --profile <profile>`
- **THEN** init SHALL not leave the profile command group in a contradictory not-installed/already-installed state
- **AND** init SHALL either enable the profile-selected module or report the exact disabled-state recovery command

