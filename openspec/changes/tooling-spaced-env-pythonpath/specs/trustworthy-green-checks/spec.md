## MODIFIED Requirements

### Requirement: Required quality gates preserve environment-manager executable paths

Required local and CI quality gates SHALL construct tool invocations so executable paths supplied by environment managers are preserved as single arguments even when those paths contain whitespace or other shell-significant characters.

#### Scenario: Shell-based type gate uses an interpreter path containing spaces

- **GIVEN** the active Python interpreter path is supplied by an environment manager and contains whitespace
- **WHEN** a shell-based required gate passes that interpreter path to a tool flag such as `--pythonpath`
- **THEN** the gate SHALL quote the path-producing command substitution or otherwise preserve it as one argument
- **AND** the downstream tool SHALL NOT receive the path split into multiple arguments

#### Scenario: Python-based gate runner builds command arguments

- **GIVEN** the active Python interpreter path is supplied by an environment manager and contains whitespace
- **WHEN** a Python-based gate runner invokes downstream tools
- **THEN** the runner SHALL pass the interpreter path as one subprocess argument rather than constructing an unquoted shell command string
