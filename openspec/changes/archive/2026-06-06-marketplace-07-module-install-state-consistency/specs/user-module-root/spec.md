## ADDED Requirements

### Requirement: Scope Diagnostics Preserve Deterministic Precedence

The system SHALL preserve project-before-user module precedence while making scope-related availability decisions explicit when they affect install or command availability.

#### Scenario: Project module shadows user module during install check

- **GIVEN** `<repo>/.specfact/modules/<module-name>` exists
- **AND** `<user-home>/.specfact/modules/<module-name>` exists
- **WHEN** the user runs `specfact module install <module-id> --scope user` from within `<repo>`
- **THEN** the command SHALL decide whether user-scope installation is satisfied using the user-scope target root
- **AND** the command SHALL warn if runtime command behavior in the current repository is still governed by the project-scope copy

#### Scenario: Project module shadows user module during missing command diagnostic

- **GIVEN** a project-scope module copy shadows a user-scope module copy with the same manifest id
- **AND** the active project-scope copy is disabled or skipped
- **WHEN** the user invokes a command group provided by that module
- **THEN** the CLI SHALL identify the active project-scope origin as the source that controls command availability
- **AND** the CLI SHALL mention that a user-scope copy exists but is shadowed in the current repository

#### Scenario: User module remains available outside project scope

- **GIVEN** a user-scope module is installed and enabled
- **AND** no project-scope copy exists in the current repository root
- **WHEN** module discovery runs from that repository
- **THEN** command availability SHALL be based on the user-scope module
- **AND** install diagnostics SHALL NOT imply that a project-scope module is required
