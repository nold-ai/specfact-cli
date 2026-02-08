# Spec: Module Packages (Delta)

## ADDED Requirements

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
