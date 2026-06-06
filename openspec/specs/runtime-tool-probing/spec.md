# runtime-tool-probing Specification

## Purpose
TBD - created by archiving change tester-cli-reliability. Update Purpose after archive.
## Requirements
### Requirement: Runtime Tool Probing Uses The Active Execution Context

Tool and install-method diagnostics SHALL prefer the active execution context over stale package-manager inventories.

#### Scenario: Upgrade launched through uv run is not classified as pipx

- **GIVEN** a machine has a pipx-installed SpecFact CLI entry in global inventory
- **AND** the current invocation is launched through `uv run specfact upgrade`
- **WHEN** install-method detection runs
- **THEN** the effective method is reported as uv-run or uv project execution
- **AND** pipx-specific spaced-home warnings are not emitted for that invocation.

#### Scenario: Semgrep available through uv is detected

- **GIVEN** a project where `uv run semgrep --version` succeeds
- **WHEN** code analysis diagnostics check semgrep availability
- **THEN** semgrep is reported as available
- **AND** the diagnostic does not tell the user to install semgrep with a pip-only command.

#### Scenario: Tool probe failures name the active manager

- **GIVEN** a required external tool is not available in the active hatch, uv, pip, or pipx context
- **WHEN** a diagnostic is emitted
- **THEN** the message names the active manager context
- **AND** the installation hint matches that manager when a manager-specific hint is known.

