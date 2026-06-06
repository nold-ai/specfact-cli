## ADDED Requirements

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
