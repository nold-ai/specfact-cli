# Spec: Module Lifecycle Management (Delta)

## ADDED Requirements

### Requirement: Registration validates ModuleIOContract implementation

The system SHALL extend registration-time validation to check if module implements ModuleIOContract and log protocol compliance status.

#### Scenario: Registration checks for protocol implementation
- **WHEN** module package is registered
- **THEN** system SHALL inspect module for ModuleIOContract implementation
- **AND** SHALL use hasattr() to check for import_to_bundle, export_from_bundle, sync_with_bundle, validate_bundle methods

#### Scenario: Full protocol implementation is logged
- **WHEN** module implements all four ModuleIOContract methods
- **THEN** registration SHALL log at INFO level: "Module X: ModuleIOContract fully implemented"
- **AND** SHALL store protocol_operations: ["import", "export", "sync", "validate"] in metadata

#### Scenario: Partial protocol implementation is logged with operations
- **WHEN** module implements only import_to_bundle and validate_bundle
- **THEN** registration SHALL log at INFO level: "Module X: ModuleIOContract partial (import, validate)"
- **AND** SHALL store protocol_operations: ["import", "validate"] in metadata

#### Scenario: No protocol implementation logs legacy mode
- **WHEN** module does not implement any ModuleIOContract methods
- **THEN** registration SHALL log at WARNING level: "Module X: No ModuleIOContract (legacy mode)"
- **AND** SHALL store protocol_operations: [] in metadata
- **AND** module SHALL still be registered for backward compatibility

### Requirement: ProjectBundle schema version compatibility check

The system SHALL extend registration validation to check ProjectBundle schema version compatibility if module declares schema_version in manifest.

#### Scenario: Compatible schema version allows registration
- **WHEN** module declares schema_version: "1" and ProjectBundle.schema_version is "1"
- **THEN** registration SHALL succeed
- **AND** SHALL log: "Module X: Schema version 1 (compatible)"

#### Scenario: Incompatible schema version skips registration
- **WHEN** module declares schema_version: "2" and ProjectBundle.schema_version is "1"
- **THEN** registration SHALL skip module
- **AND** SHALL log at WARNING level: "Module X: Schema version 2 required, but current is 1 (skipped)"
- **AND** skipped module SHALL be listed in registration summary

#### Scenario: Missing schema version assumes compatibility
- **WHEN** module omits schema_version from manifest
- **THEN** registration SHALL assume current ProjectBundle schema
- **AND** SHALL log at DEBUG level: "Module X: No schema version declared (assuming current)"
- **AND** module SHALL be registered normally

### Requirement: Registration summary includes protocol compliance

The system SHALL extend registration summary output to include protocol compliance statistics.

#### Scenario: Summary counts protocol-compliant modules
- **WHEN** registration completes
- **THEN** summary SHALL include counts: "Protocol-compliant: 4/5 modules"
- **AND** SHALL list modules by status: Full (3), Partial (1), Legacy (1)

#### Scenario: Summary warns about legacy modules
- **WHEN** registration finds modules without ModuleIOContract
- **THEN** summary SHALL include warning: "1 module(s) in legacy mode (no ModuleIOContract)"
- **AND** SHALL recommend updating to ModuleIOContract for marketplace compatibility
