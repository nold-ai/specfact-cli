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

### Requirement: Module package manifests declare service bridges

The system SHALL allow `module-package.yaml` to declare `service_bridges` metadata for converter registration.

#### Scenario: Manifest includes service bridge declaration

- **WHEN** a module manifest includes `service_bridges`
- **THEN** each bridge entry SHALL include `id` and `converter_class`
- **AND** optional metadata such as `description` MAY be provided.

#### Scenario: Manifest without service bridges remains valid

- **WHEN** a legacy module manifest omits `service_bridges`
- **THEN** manifest validation SHALL still pass
- **AND** module lifecycle SHALL treat the module as having no bridge declarations.

### Requirement: Service bridge metadata is validated during manifest parsing

The system SHALL validate service bridge metadata structure before module registration.

#### Scenario: Invalid bridge metadata is rejected for registration

- **WHEN** a bridge entry is missing required keys or has malformed converter path
- **THEN** parser validation SHALL flag the declaration as invalid
- **AND** module registration SHALL skip only invalid bridge declarations.

#### Scenario: Valid bridge metadata is preserved in package model

- **WHEN** a manifest contains valid bridge declarations
- **THEN** the parsed `ModulePackageMetadata` SHALL expose those declarations for lifecycle registration.

### Requirement: Protocol metadata reflects real module operations

The system SHALL derive protocol operation metadata from the effective module interface used at runtime.

#### Scenario: Protocol operations are populated from runtime-accessible module interface

- **WHEN** module metadata is loaded for an enabled module
- **THEN** protocol operation detection SHALL inspect the runtime-accessible interface used by lifecycle registration
- **AND** detected operations SHALL be persisted in `ModulePackageMetadata.protocol_operations`.

### Requirement: Module package manifest SHALL support publisher and integrity metadata

The system SHALL support structured publisher and integrity metadata in `module-package.yaml`.

#### Scenario: Manifest includes publisher identity

- **WHEN** manifest includes `publisher` metadata
- **THEN** parser SHALL capture `name`, `email`, and optional publisher attributes
- **AND** parsed metadata SHALL be available to trust-validation workflows.

#### Scenario: Manifest includes integrity metadata

- **WHEN** manifest includes `integrity` metadata
- **THEN** parser SHALL capture checksum and optional signature fields
- **AND** validation SHALL ensure checksum format correctness.

### Requirement: Manifest dependencies SHALL support versioned entries

The system SHALL support versioned dependency declarations for both module and pip dependencies.

#### Scenario: Versioned module dependency parsed

- **WHEN** manifest declares module dependency with name and version specifier
- **THEN** parser SHALL store both values in typed metadata
- **AND** version specifier SHALL be validated as a supported constraint format.

#### Scenario: Versioned pip dependency parsed

- **WHEN** manifest declares pip dependency with name and version specifier
- **THEN** parser SHALL preserve versioned dependency for installation-time resolution
- **AND** legacy list formats SHALL remain backward compatible when possible.

### Requirement: Module manifest declares schema extensions

The system SHALL extend `ModulePackageMetadata` to include optional `schema_extensions` field declaring fields the module adds to core models.

#### Scenario: Manifest schema includes schema_extensions

- **WHEN** module-package.yaml is parsed
- **THEN** it MAY include `schema_extensions` array
- **AND** each entry SHALL specify: target model name, field definitions with type/description

#### Scenario: Schema extension for Feature model

- **WHEN** module declares schema_extensions for Feature
- **THEN** manifest SHALL list fields being added
- **AND** each field SHALL include type hint and description
- **AND** module namespace is implicit from module name

#### Scenario: Schema extension for ProjectBundle model

- **WHEN** module declares schema_extensions for ProjectBundle
- **THEN** manifest SHALL list fields being added
- **AND** each field SHALL include type hint and description

#### Scenario: Module without schema_extensions remains valid

- **WHEN** module-package.yaml omits schema_extensions
- **THEN** module SHALL load successfully
- **AND** no extensions registered for that module

### Requirement: Module discovery supports multiple source locations

The system SHALL extend module discovery to scan built-in, marketplace, and custom paths with source tracking.

#### Scenario: Discovery function returns source information

- **WHEN** discover_package_metadata() finds a module
- **THEN** it SHALL include source field in metadata
- **AND** source SHALL be "builtin", "marketplace", or "custom"

#### Scenario: Registry stores module source

- **WHEN** module is registered
- **THEN** registry SHALL persist source information
- **AND** SHALL be queryable via module list command
