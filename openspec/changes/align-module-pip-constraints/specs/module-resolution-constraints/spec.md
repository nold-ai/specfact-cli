## ADDED Requirements

### Requirement: Resolve and install with the same pip constraints

When the caller supplies pip constraint files through `PIP_CONSTRAINT`, SpecFact SHALL apply those same constraints to pip-compile and pip installation. Conflicting requirements SHALL fail through the existing resolver without bypassing dependency or module checks.

#### Scenario: An installed module inherits a reviewed dependency pin

- **GIVEN** a module allows multiple versions and the caller constrains one supported version through pip
- **WHEN** the dependency resolver uses pip-compile before installation
- **THEN** it passes the same constraint files to the compiler and the resolved version is accepted by the installer
- **AND** package source options in the constraints file are applied by pip while only resolved requirements are passed as install arguments
