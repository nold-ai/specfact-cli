## ADDED Requirements

### Requirement: Automatic pip installation uses only verified selected metadata

The marketplace installer SHALL verify the selected artifact before dependency processing and SHALL use only that artifact's pip dependency declarations as resolver and installer input.

#### Scenario: Project module cannot inject a dependency

- **GIVEN** discovery includes a project module with a pip dependency
- **WHEN** an unrelated marketplace module is installed
- **THEN** the project dependency is not passed to dependency resolution or pip installation

#### Scenario: Integrity failure has no dependency side effects

- **GIVEN** a downloaded marketplace artifact fails integrity verification
- **WHEN** installation is attempted
- **THEN** neither bundle dependencies nor pip dependencies are installed

### Requirement: Automatic requirements exclude executable pip input forms

Automatic marketplace dependency installation SHALL accept only valid PEP 508 named requirements without direct URL or VCS references and SHALL reject pip options and local paths before invoking pip.

#### Scenario: Unsafe requirement is rejected

- **GIVEN** a selected artifact declares a direct URL, VCS URL, local path, or pip option
- **WHEN** dependency handling begins
- **THEN** installation fails before any pip resolver or installer subprocess receives the requirement

#### Scenario: Named requirement remains supported

- **GIVEN** a selected verified artifact declares a named requirement with extras, markers, and version constraints
- **WHEN** dependency handling begins
- **THEN** the requirement may be resolved and installed normally
