# module-packages Specification

## Purpose
TBD - created by archiving change arch-01-cli-modular-command-registry. Update Purpose after archive.
## Requirements
### Requirement: Logical Packages by Feature with Dedicated Folder Structure

The CLI SHALL group functionality into **logical module packages** by feature (e.g. "backlog refine", "backlog daily", "validate sidecar"). Each package SHALL live in a dedicated folder under a modules root and SHALL include its own **metadata**, **src**, **resources** (prompts, templates), and **tests**. Resources that are used only by one feature SHALL belong to that package; shared resources remain in core or a shared package.

**Rationale**: Prepares for an extensible ecosystem and future selective install; keeps each feature self-contained and versionable.

#### Scenario: Package Has Metadata and Standard Layout

**Given**: A module package "backlog_refine" exists under the modules root

**When**: Discovery runs (e.g. at startup or on specfact init)

**Then**: The package folder contains at least: `module-package.yaml` (with name, version, commands list, optional pip_dependencies and module_dependencies), `src/` (Python code for the feature), and optionally `resources/` (prompts, templates) and `tests/`

**Acceptance Criteria**:

- module-package.yaml is valid and includes: name, version, commands (list of command names this package provides)
- metadata MAY include: pip_dependencies, module_dependencies, tier, addon_id
- Package loader loads only that package's src (and its resources); no hard dependency on flat commands/ or resources/ layout for that feature

#### Scenario: Discovery Registers Packages with Registry

**Given**: Modules root contains one or more package folders with valid module-package.yaml

**When**: Module discovery runs

**Then**: Each package is registered with the CommandRegistry (or equivalent) so that each command name in package metadata is resolvable via the registry; the loader for that command loads only that package's code and resources

**Acceptance Criteria**:

- Registry receives entries for all commands listed in discovered package metadata
- Invoking a command loads only the package that provides it (and its dependencies if any)
- Design does not block future selective install (metadata and layout support filtering by installed packages later)

---

### Requirement: Core vs Package Grouping

The codebase SHALL distinguish **core** (bootstrapping, CommandRegistry, init scaffolding, auth/runtime/config, shared utils and models) from **module packages** (feature-specific commands and their resources). Moving existing code and resources into package folders MAY be incremental (e.g. one package at a time) but the structure and discovery SHALL support the target state.

**Rationale**: Keeps core stable; allows packages to be developed and versioned independently.

#### Scenario: Core Does Not Depend on Feature-Specific Resources

**Given**: Core is defined as registry, init (scaffolding), auth, runtime, shared utils/models

**When**: Core runs (e.g. discovery, root help from cache)

**Then**: Core does not import feature-specific prompts or templates from a flat resources/ folder; feature-specific resources are loaded only when the package that owns them is loaded

**Acceptance Criteria**:

- Package loaders resolve resources relative to their package folder (e.g. package resources/ or templates/)
- Shared resources (used by more than one package) may remain in a shared location or core until further refactor

### Requirement: Module package metadata includes schema_version field

The system SHALL extend `ModulePackageMetadata` to include a `schema_version` field indicating which ProjectBundle schema version the module is compatible with.

#### Scenario: Metadata declares schema compatibility
- **WHEN** module-package.yaml is loaded
- **THEN** it MAY include `schema_version: "1"` field
- **AND** module registration SHALL validate compatibility with ProjectBundle.schema_version

#### Scenario: Missing schema_version defaults to current
- **WHEN** module-package.yaml omits schema_version
- **THEN** registration SHALL assume current ProjectBundle schema version
- **AND** SHALL log warning recommending explicit declaration

#### Scenario: Incompatible schema_version blocks registration
- **WHEN** module declares schema_version: "2" but ProjectBundle is version "1"
- **THEN** registration SHALL skip module with warning
- **AND** SHALL log: "Module X requires schema version 2, but current is 1"

### Requirement: Module discovery validates ModuleIOContract implementation

The system SHALL extend module discovery to check if module implements ModuleIOContract protocol and log supported operations.

#### Scenario: Discovery detects protocol implementation
- **WHEN** module package is discovered and loaded
- **THEN** registry SHALL check if module class implements ModuleIOContract
- **AND** SHALL use hasattr() to detect which operations are supported

#### Scenario: Module with protocol is logged as compliant
- **WHEN** module implements all four ModuleIOContract methods
- **THEN** registration SHALL log: "Module X implements ModuleIOContract (full)"
- **AND** SHALL store supported operations in module metadata

#### Scenario: Module without protocol is logged as legacy
- **WHEN** module does not implement ModuleIOContract
- **THEN** registration SHALL log warning: "Module X does not implement ModuleIOContract (legacy mode)"
- **AND** SHALL still register module for backward compatibility

#### Scenario: Module with partial protocol is logged with operations
- **WHEN** module implements import_to_bundle and validate_bundle only
- **THEN** registration SHALL log: "Module X implements ModuleIOContract (partial: import, validate)"
- **AND** SHALL allow partial implementation

### Requirement: Module metadata schema updated in models

The system SHALL update `src/specfact_cli/models/module_package.py` to include schema_version and protocol_compliance fields.

#### Scenario: ModulePackageMetadata has schema_version field
- **WHEN** ModulePackageMetadata is instantiated
- **THEN** it SHALL have optional `schema_version: str | None` field
- **AND** default value SHALL be None (implying current schema)

#### Scenario: ModulePackageMetadata tracks protocol operations
- **WHEN** module is discovered
- **THEN** metadata SHALL have `protocol_operations: list[str]` field
- **AND** SHALL contain names of implemented operations: ["import", "export", "sync", "validate"]

