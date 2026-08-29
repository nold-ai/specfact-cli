## MODIFIED Requirements

### Requirement: Module doctor reports effective and shadowed module copies

The system SHALL provide module-scope diagnostics that report module origin, version, path, and shadowing state without importing module command code or treating a valid lower-priority installation as stale by default.

#### Scenario: Duplicate project and user module copies are visible

- **GIVEN** a module id exists in project scope and user scope with different versions
- **WHEN** the user runs `specfact module doctor <module-id>`
- **THEN** the output identifies the project copy as effective
- **AND** the output identifies the user copy as shadowed
- **AND** the output shows both versions and paths
- **AND** the output states that the user-scoped copy remains installed
- **AND** the output states that normal shadowing alone does not require uninstalling it
- **AND** any claim about use outside the current workspace accounts for the module's enabled state and other higher-priority copies
- **AND** the output does not recommend uninstalling the user-scoped copy

#### Scenario: Runtime discovery reports project-over-user precedence

- **GIVEN** a module id exists in project scope and user scope
- **WHEN** runtime discovery selects the project-scoped copy
- **THEN** the diagnostic identifies project scope as effective in the current workspace
- **AND** it states that the user-scoped copy remains installed
- **AND** it does not claim that the user copy is active outside the workspace without accounting for module state and other higher-priority copies
- **AND** it does not recommend uninstalling the user-scoped copy

#### Scenario: Doctor identifies the actual effective source

- **GIVEN** a user-scoped module is shadowed by a higher-priority copy
- **WHEN** the user runs `specfact module doctor <module-id>`
- **THEN** the guidance identifies the actual effective source
- **AND** it does not describe built-in, marketplace, or custom shadowing as project precedence

#### Scenario: Development source roots are disclosed

- **GIVEN** development source root environment variables are configured
- **WHEN** the user runs `specfact module doctor`
- **THEN** the output lists the configured development source roots that may influence import resolution
