## ADDED Requirements

### Requirement: Project module code requires verified provenance

The CLI SHALL NOT register executable commands from a project-scoped module unless the artifact has valid integrity metadata and a signature verifiable with configured trusted key material, or the operator explicitly enables unsigned modules.

#### Scenario: Unsigned project module is discovered by default

- **GIVEN** a repository contains a project-scoped module with executable Python and no integrity metadata
- **AND** unsigned modules have not been explicitly allowed
- **WHEN** module package commands are registered
- **THEN** the module command is skipped
- **AND** resolving CLI help does not execute the project module Python

#### Scenario: Operator explicitly allows unsigned project development

- **GIVEN** a project-scoped module has no signature
- **AND** the operator explicitly enables the unsigned-module override
- **WHEN** module package commands are registered
- **THEN** existing unsigned development behavior is preserved

#### Scenario: Signed project module fails trusted-key verification

- **GIVEN** a project-scoped module carries integrity metadata signed by an untrusted key
- **WHEN** module package commands are registered without the unsigned override
- **THEN** the module command is skipped
