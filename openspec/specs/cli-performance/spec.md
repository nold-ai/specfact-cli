# cli-performance Specification

## Purpose

TBD - created by archiving change optimize-startup-performance. Update Purpose after archive.

## Requirements

### Requirement: Metadata-Based Startup Check Optimization

The CLI SHALL track version and check timestamps in metadata to optimize startup performance.

#### Scenario: Version-based template check skipping

- **Given** the CLI has metadata file `~/.specfact/metadata.json` with `last_checked_version` set to current version
- **When** the CLI starts up
- **Then** IDE template checks are skipped (not executed)
- **And** startup completes faster

#### Scenario: Template check after version update

- **Given** the CLI version has changed since last check (current version != `last_checked_version` in metadata)
- **When** the CLI starts up
- **Then** IDE template checks are executed
- **And** metadata is updated with new version

#### Scenario: First-time user template check

- **Given** no metadata file exists (`~/.specfact/metadata.json` not found)
- **When** the CLI starts up
- **Then** IDE template checks are executed (first-time setup)
- **And** metadata file is created with current version

### Requirement: Rate-Limited Version Checking

The CLI SHALL check PyPI for version updates only once per day, not on every startup.

#### Scenario: Version check skipping within 24 hours

- **Given** the CLI has metadata with `last_version_check_timestamp` less than 24 hours ago
- **When** the CLI starts up
- **Then** PyPI version check is skipped
- **And** startup completes faster

#### Scenario: Version check after 24 hours

- **Given** the CLI has metadata with `last_version_check_timestamp` >= 24 hours ago
- **When** the CLI starts up
- **Then** PyPI version check is executed
- **And** metadata is updated with current timestamp

#### Scenario: First-time user version check

- **Given** no metadata file exists
- **When** the CLI starts up
- **Then** PyPI version check is executed (first-time setup)
- **And** metadata file is created with current timestamp

### Requirement: Manual Update Command

The CLI SHALL provide a dedicated command for checking and installing updates.

#### Scenario: Check for updates

- **Given** the user runs `specfact update --check-only`
- **When** an update is available on PyPI
- **Then** the CLI displays current and latest version
- **And** update instructions are shown
- **And** no installation is performed

#### Scenario: Install update via pip

- **Given** specfact-cli was installed via pip
- **And** the user runs `specfact update --yes`
- **When** an update is available
- **Then** the CLI executes `pip install --upgrade specfact-cli`
- **And** the update is installed successfully

#### Scenario: Install update via pipx

- **Given** specfact-cli was installed via pipx
- **And** the user runs `specfact update --yes`
- **When** an update is available
- **Then** the CLI executes `pipx upgrade specfact-cli`
- **And** the update is installed successfully

#### Scenario: Install update via uvx

- **Given** specfact-cli is used via uvx
- **And** the user runs `specfact update --check-only`
- **When** an update is available
- **Then** the CLI shows instructions to use `uvx specfact-cli@latest`
- **And** no automatic installation is attempted

### Requirement: Startup Performance Target

The CLI SHALL respond within 1-2 seconds maximum on startup.

#### Scenario: Fast startup with checks skipped

- **Given** metadata indicates checks should be skipped
- **When** the CLI starts up
- **Then** startup completes within 2 seconds
- **And** no blocking operations > 100ms occur

#### Scenario: Acceptable startup with checks

- **Given** metadata indicates checks should run
- **When** the CLI starts up
- **Then** startup completes within 2 seconds
- **And** checks complete asynchronously or with timeout

### Requirement: Startup Check Execution

The startup check execution logic SHALL be conditional based on metadata.

#### Scenario: Conditional check execution

- **Given** the CLI has metadata tracking
- **When** `print_startup_checks()` is called
- **Then** checks are executed only when metadata conditions are met
- **And** metadata is updated after checks complete
