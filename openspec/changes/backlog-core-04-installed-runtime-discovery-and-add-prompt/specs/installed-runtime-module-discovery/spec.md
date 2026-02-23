## MODIFIED Requirements

### Requirement: Module Discovery Roots

The system SHALL discover module packages consistently between development and installed runtime contexts when invoked from a repository checkout.

#### Scenario: Installed runtime discovers workspace modules from repo root

- **GIVEN** `specfact` is installed from PyPI/site-packages
- **AND** the current working directory contains `modules/` with valid module packages
- **WHEN** module discovery runs
- **THEN** discovery includes the current working directory `modules/` root
- **AND** commands contributed by those modules are available without requiring `SPECFACT_MODULES_ROOTS`.

#### Scenario: No cwd modules directory keeps existing behavior

- **GIVEN** the current working directory does not contain a `modules/` directory
- **WHEN** module discovery runs
- **THEN** discovery roots remain limited to packaged modules and explicitly configured roots
- **AND** no extra discovery errors are introduced.
