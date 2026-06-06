## ADDED Requirements

### Requirement: Environment Manager Detection Supports Rootless Monorepos

The system SHALL detect supported Python environment managers in repositories that do not have a root-level Python project file but do contain package-level project files.

#### Scenario: Rootless monorepo with uv package files

- **GIVEN** a repository root has no `pyproject.toml`
- **AND** a first-level package directory contains `pyproject.toml`
- **AND** `uv` is available on `PATH`
- **WHEN** environment manager detection runs for the repository root
- **THEN** the detected manager is `uv`
- **AND** the command prefix is `uv run`
- **AND** `specfact init ide` does not report "No Compatible Environment Manager Detected"

#### Scenario: Rootless monorepo with nested uv lock

- **GIVEN** a repository root has no `pyproject.toml`
- **AND** a first-level or second-level package directory contains `uv.lock` or `uv.toml`
- **AND** `uv` is available on `PATH`
- **WHEN** environment manager detection runs for the repository root
- **THEN** the detected manager is `uv`

### Requirement: Environment Manager Detection Falls Back To PATH Tools

When no project marker identifies an environment manager, the system SHALL detect supported tools available on `PATH` before returning `unknown`.

#### Scenario: PATH-only uv detection

- **GIVEN** a repository has no supported root or package-level Python project marker
- **AND** `uv` is available on `PATH`
- **WHEN** environment manager detection runs
- **THEN** the detected manager is `uv`
- **AND** the command prefix is `uv run`

#### Scenario: No markers or tools remain unknown

- **GIVEN** a repository has no supported Python project marker
- **AND** no supported environment manager executable is available on `PATH`
- **WHEN** environment manager detection runs
- **THEN** the detected manager remains `unknown`
- **AND** existing direct-invocation fallback behavior is preserved
