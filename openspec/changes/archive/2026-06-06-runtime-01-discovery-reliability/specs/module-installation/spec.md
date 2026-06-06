## ADDED Requirements

### Requirement: Missing Command Diagnostics Explain Installed-Unavailable Causes

When a known module-provided command group is not registered, the system SHALL distinguish an absent module from an installed module that is unavailable for another local reason.

#### Scenario: Missing command provider fails during lazy command load

- **GIVEN** a known command group is provided by an installed and enabled module
- **AND** the module command app cannot be imported because a runtime dependency or module package import is missing
- **WHEN** the user invokes the command group
- **THEN** the CLI SHALL report that the module is installed but unavailable
- **AND** the diagnostic SHALL include the failing load reason when it can be captured without retrying destructive installation
- **AND** the diagnostic SHALL NOT report only that the module is not installed
