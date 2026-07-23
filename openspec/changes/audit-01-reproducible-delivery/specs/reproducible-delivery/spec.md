## ADDED Requirements

### Requirement: Blocking delivery uses immutable dependency resolution

Blocking CI and release validation SHALL create Python environments from a committed frozen resolution and SHALL reject lock or export drift.

#### Scenario: Blocking job validates a changed dependency declaration

- **WHEN** a pull request changes `pyproject.toml`, `uv.lock`, or the CI dependency export
- **THEN** CI SHALL verify that the export was generated from the committed lock
- **AND** SHALL install the locked dependencies without resolving a replacement graph
- **AND** SHALL fail before release proof when the lock or export is stale.

#### Scenario: Wheel smoke avoids a second resolution

- **WHEN** a blocking runtime validation job builds the package wheel
- **THEN** it SHALL install that wheel with dependency resolution disabled into the prepared frozen environment
- **AND** SHALL report the lock identity with the validation artifacts.

### Requirement: Blocking module integration uses an immutable fixture

The modules repository used by blocking runtime validation SHALL be selected by reviewed commit SHA rather than branch name.

#### Scenario: Runtime fixture is checked out

- **WHEN** blocking package-runtime validation starts
- **THEN** it SHALL read the modules repository URL and full commit SHA from a versioned fixture lock
- **AND** SHALL verify the checked-out `HEAD` equals that SHA before executing module commands
- **AND** SHALL fail if the lock contains a branch or mutable ref.

### Requirement: Declared Python versions receive locked wheel smoke proof

The supported Python versions 3.11, 3.12, and 3.13 SHALL each execute built-wheel smoke validation from the frozen resolution.

#### Scenario: A supported interpreter runs the matrix

- **WHEN** package, runtime, module-discovery, or workflow paths change
- **THEN** the blocking runtime matrix SHALL run the built-wheel smoke suite on Python 3.11, 3.12, and 3.13
- **AND** a failure on any declared interpreter SHALL block the pull request.

### Requirement: Compatibility discovery remains clearly advisory

The repository SHALL retain a scheduled/manual lower-bound or latest-resolution compatibility lane that cannot satisfy blocking release evidence.

#### Scenario: Advisory resolver compatibility fails

- **WHEN** the scheduled compatibility lane detects a dependency-resolution failure
- **THEN** its output SHALL identify the resolved graph and label the result advisory
- **AND** branch protection SHALL not treat that run as the immutable delivery proof.
