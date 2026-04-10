# init-module-discovery-alignment Specification

## Purpose

TBD - created by archiving change backlog-core-01-dependency-analysis-commands. Update Purpose after archive.

## Requirements

### Requirement: Init uses same discovery roots as registry

The system SHALL use the same module discovery roots for `specfact init` module state and list operations as are used for command registration (built-in package modules, repo-root `modules/` when present, and `SPECFACT_MODULES_ROOTS` when set).

**Rationale**: Workspace-level modules (e.g. `modules/backlog-core/`) are discovered at runtime for commands but were previously invisible to init; aligning discovery ensures enable/disable and list-modules operate on the same set.

#### Scenario: Init list-modules includes workspace-level modules

**Given** the repository has a workspace-level module at `modules/<name>/` with valid `module-package.yaml`

**When** the user runs `specfact init --list-modules`

**Then** the output SHALL include that module (id, version, enabled) in the same way as built-in modules

**And** the module SHALL be eligible for `--enable-module` and `--disable-module`

#### Scenario: Enable/disable validation uses full discovered set

**Given** workspace-level and built-in modules are discovered

**When** the user runs `specfact init --enable-module <id>` or `--disable-module <id>` for a workspace-level module

**Then** the init command SHALL validate enable/disable against the full discovered package set (not built-in only)

**And** state SHALL be persisted so the module's enabled flag is respected on next init and at command registration
