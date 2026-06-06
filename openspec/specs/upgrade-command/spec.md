# upgrade-command Specification

## Purpose

TBD - created by archiving change upgrade-01-install-method-aware. Update Purpose after archive.
## Requirements
### Requirement: Upgrade command must respect installation method

`specfact upgrade` SHALL detect whether SpecFact is installed via pip, pipx, uv, or uvx and present/execute an installation-method-appropriate upgrade command. When a pipx upgrade succeeds, the command SHALL suppress the known benign pipx warning block about spaces in `PIPX_HOME`. When a pipx upgrade fails, the command SHALL preserve child-process stdout and stderr diagnostics. When an upgrade times out after producing partial child-process output, the command SHALL replay the partial diagnostics before reporting the timeout.

#### Scenario: Successful pipx upgrade suppresses spaced-home warning

- **GIVEN** SpecFact detects a pipx installation
- **AND** `pipx upgrade specfact-cli` exits successfully
- **AND** pipx emits its warning block about a space in the pipx home path
- **WHEN** `specfact upgrade` runs the update
- **THEN** the user-visible output does not include the spaced-home warning block
- **AND** the upgrade still reports success.

#### Scenario: Failed pipx upgrade preserves diagnostics

- **GIVEN** SpecFact detects a pipx installation
- **AND** `pipx upgrade specfact-cli` exits with a non-zero status
- **AND** pipx emits stdout or stderr diagnostics
- **WHEN** `specfact upgrade` handles the failed update
- **THEN** the user-visible output includes the child-process diagnostics
- **AND** the upgrade reports failure.

#### Scenario: Timed-out upgrade preserves partial diagnostics

- **GIVEN** an installation-method-appropriate upgrade command starts
- **AND** the child process emits stdout or stderr diagnostics before exceeding the timeout
- **WHEN** `specfact upgrade` handles the timed-out update
- **THEN** the user-visible output includes the partial child-process diagnostics
- **AND** the upgrade reports the timeout.

