# schema-extension-system Specification

## Purpose

TBD - created by archiving change arch-07-schema-extension-system. Update Purpose after archive.

## Requirements

### Requirement: Core models provide extensions field

The system SHALL add an `extensions` field to Feature and ProjectBundle models to store module-specific metadata as a dictionary with namespace-prefixed keys.

#### Scenario: Feature model includes extensions field

- **WHEN** Feature model is instantiated
- **THEN** it SHALL include `extensions: dict[str, Any]` field
- **AND** extensions SHALL default to empty dict if not provided
- **AND** extensions SHALL serialize/deserialize with YAML and JSON

#### Scenario: ProjectBundle model includes extensions field

- **WHEN** ProjectBundle model is instantiated
- **THEN** it SHALL include `extensions: dict[str, Any]` field
- **AND** extensions SHALL default to empty dict if not provided
- **AND** extensions SHALL serialize/deserialize with YAML and JSON

#### Scenario: Backward compatibility with bundles without extensions

- **WHEN** existing bundle without extensions field is loaded
- **THEN** extensions SHALL default to empty dict
- **AND** bundle SHALL remain valid
- **AND** no migration required

### Requirement: Type-safe extension accessors with namespace enforcement

The system SHALL provide `get_extension()` and `set_extension()` methods on Feature and ProjectBundle models that enforce namespace-prefixed field access.

#### Scenario: Get extension with namespace prefix

- **WHEN** code calls `feature.get_extension("backlog", "ado_work_item_id")`
- **THEN** system SHALL look up `extensions["backlog.ado_work_item_id"]`
- **AND** SHALL return the value if present
- **AND** SHALL return None if not present (or provided default)

#### Scenario: Set extension with namespace prefix

- **WHEN** code calls `feature.set_extension("backlog", "ado_work_item_id", "123456")`
- **THEN** system SHALL store value at `extensions["backlog.ado_work_item_id"]`
- **AND** SHALL enforce namespace format (module.field)

#### Scenario: Invalid namespace format is rejected

- **WHEN** code calls `set_extension("backlog.submodule", "field", "value")`
- **THEN** system SHALL raise ValueError with message "Invalid module name format"
- **AND** SHALL require single-level namespace (no dots in module_name)

#### Scenario: Get extension with default value

- **WHEN** code calls `feature.get_extension("backlog", "missing_field", default="default_value")`
- **THEN** system SHALL return "default_value" if field not present
- **AND** SHALL NOT modify extensions dict

### Requirement: Module manifest declares schema extensions

The system SHALL extend module manifest schema to allow modules to declare schema extensions in `module-package.yaml`.

#### Scenario: Manifest declares Feature extensions

- **WHEN** module-package.yaml includes schema_extensions section
- **THEN** it MAY declare extensions for Feature model
- **AND** each extension SHALL specify: target (Feature), field name, type hint, description

#### Scenario: Manifest declares ProjectBundle extensions

- **WHEN** module-package.yaml includes schema_extensions section
- **THEN** it MAY declare extensions for ProjectBundle model
- **AND** each extension SHALL specify: target (ProjectBundle), field name, type hint, description

#### Scenario: Extension field metadata is documented

- **WHEN** module declares schema extension
- **THEN** manifest SHALL include human-readable description
- **AND** description SHALL explain purpose and usage
- **AND** type hint SHALL guide consumers (documentation only, not enforced)

### Requirement: Namespace collision detection at registration

The system SHALL validate that no two modules declare conflicting extension field names during module registration.

#### Scenario: Duplicate extension field is detected

- **WHEN** module A declares extension "backlog.ado_work_item_id"
- **AND** module B also declares extension "backlog.ado_work_item_id"
- **THEN** registration SHALL fail for second module
- **AND** SHALL log error: "Extension field collision: backlog.ado_work_item_id already declared by module A"

#### Scenario: Different modules use unique namespaces

- **WHEN** module backlog declares "backlog.ado_work_item_id"
- **AND** module sync declares "sync.last_sync_timestamp"
- **THEN** both registrations SHALL succeed
- **AND** no collision detected

#### Scenario: Same module declares multiple fields

- **WHEN** module backlog declares "backlog.ado_work_item_id" and "backlog.jira_issue_key"
- **THEN** both extensions SHALL register successfully
- **AND** namespace "backlog" is owned by backlog module

### Requirement: Extension registry for introspection

The system SHALL maintain a global extension registry mapping module names to their declared schema extensions for debugging and documentation.

#### Scenario: Registry populated at module registration

- **WHEN** module registration loads schema_extensions from manifest
- **THEN** extensions SHALL be added to global registry
- **AND** registry SHALL map: module_name → list of (target, field, type, description)

#### Scenario: Registry is queryable for debugging

- **WHEN** developer needs to inspect registered extensions
- **THEN** registry SHALL provide method to list all extensions
- **AND** SHALL show which module declared each extension
- **AND** SHALL be accessible via debug logging or introspection

### Requirement: Contract enforcement with icontract

The system SHALL use @icontract decorators to enforce namespace format and type safety for extension operations.

#### Scenario: get_extension enforces namespace format

- **WHEN** get_extension() is called
- **THEN** @require SHALL validate module_name matches pattern `[a-z][a-z0-9_-]*`
- **AND** @require SHALL validate field matches pattern `[a-z][a-z0-9_]*`
- **AND** SHALL use @beartype for type checking

#### Scenario: set_extension enforces namespace format

- **WHEN** set_extension() is called
- **THEN** @require SHALL validate module_name and field patterns
- **AND** @ensure SHALL verify value was stored at correct key
- **AND** SHALL use @beartype for type checking

### Requirement: Extensions are optional and non-breaking

The system SHALL ensure extension functionality does not break existing code that does not use extensions.

#### Scenario: Core operations work without extensions

- **WHEN** bundle is created without any extension usage
- **THEN** all core operations SHALL function normally
- **AND** extensions field SHALL be empty dict
- **AND** no performance impact

#### Scenario: Modules without schema_extensions work normally

- **WHEN** module manifest omits schema_extensions section
- **THEN** module SHALL register successfully
- **AND** module SHALL function normally
- **AND** SHALL NOT have any extensions registered
