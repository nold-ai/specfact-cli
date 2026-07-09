# module-io-contract Specification

## Purpose

TBD - created by archiving change arch-04-core-contracts-interfaces. Update Purpose after archive.

## Requirements

### Requirement: ModuleIOContract protocol defines four core operations

The system SHALL provide a `ModuleIOContract` Protocol in `src/specfact_cli/contracts/module_interface.py` that defines four required operations all modules must implement for interacting with ProjectBundle.

#### Scenario: Protocol defines import_to_bundle operation

- **WHEN** a module implements ModuleIOContract
- **THEN** it MUST provide `import_to_bundle(source: Path, config: dict) -> ProjectBundle` method that converts external format to ProjectBundle

#### Scenario: Protocol defines export_from_bundle operation

- **WHEN** a module implements ModuleIOContract
- **THEN** it MUST provide `export_from_bundle(bundle: ProjectBundle, target: Path, config: dict) -> None` method that converts ProjectBundle to external format

#### Scenario: Protocol defines sync_with_bundle operation

- **WHEN** a module implements ModuleIOContract
- **THEN** it MUST provide `sync_with_bundle(bundle: ProjectBundle, external_source: str, config: dict) -> ProjectBundle` method for bidirectional synchronization

#### Scenario: Protocol defines validate_bundle operation

- **WHEN** a module implements ModuleIOContract
- **THEN** it MUST provide `validate_bundle(bundle: ProjectBundle, rules: dict) -> ValidationReport` method for module-specific validation

### Requirement: Protocol uses structural subtyping

The system SHALL use `typing.Protocol` for ModuleIOContract to enable structural subtyping without requiring explicit inheritance.

#### Scenario: Module without explicit inheritance satisfies protocol

- **WHEN** a module class implements all four protocol methods with correct signatures
- **THEN** basedpyright type checker SHALL recognize it as implementing ModuleIOContract
- **AND** no explicit inheritance or registration is required

#### Scenario: Module with partial implementation is type-checked

- **WHEN** a module class implements only some protocol methods
- **THEN** basedpyright SHALL report protocol violations during type checking
- **AND** module registration SHALL detect missing methods via hasattr() checks

### Requirement: Protocol methods use ProjectBundle as sole IO contract

The system SHALL enforce that all ModuleIOContract methods accept or return ProjectBundle as the data exchange format.

#### Scenario: Import operation returns ProjectBundle

- **WHEN** import_to_bundle is called with valid external source
- **THEN** it MUST return a ProjectBundle instance
- **AND** the returned bundle SHALL have all required fields populated

#### Scenario: Export operation accepts ProjectBundle

- **WHEN** export_from_bundle is called with ProjectBundle
- **THEN** it MUST accept ProjectBundle as input
- **AND** SHALL NOT require any other data structure for core export logic

#### Scenario: Sync operation uses ProjectBundle bidirectionally

- **WHEN** sync_with_bundle is called
- **THEN** it MUST accept ProjectBundle as input
- **AND** MUST return ProjectBundle as output
- **AND** SHALL NOT use intermediate formats bypassing ProjectBundle

### Requirement: Protocol methods have icontract decorators

The system SHALL require all ModuleIOContract implementations to use `@icontract` and `@beartype` decorators for runtime validation.

#### Scenario: Import method has preconditions

- **WHEN** import_to_bundle is implemented
- **THEN** it MUST have `@require` decorator validating source path exists
- **AND** MUST have `@beartype` decorator for type checking

#### Scenario: Export method has postconditions

- **WHEN** export_from_bundle is implemented
- **THEN** it MUST have `@ensure` decorator validating target file was created
- **AND** MUST have `@beartype` decorator for type checking

#### Scenario: Validate method returns ValidationReport

- **WHEN** validate_bundle is implemented
- **THEN** it MUST return ValidationReport instance
- **AND** MUST have `@ensure` decorator validating report structure

### Requirement: Protocol supports optional operation subsets

The system SHALL allow modules to implement subsets of ModuleIOContract operations based on their functionality.

#### Scenario: Import-only module omits export methods

- **WHEN** a module only supports importing from external systems
- **THEN** it MAY implement only import_to_bundle and validate_bundle
- **AND** module registration SHALL detect and log supported operations

#### Scenario: Sync-only module implements full bidirectional operations

- **WHEN** a module supports bidirectional sync
- **THEN** it MUST implement all four operations
- **AND** sync_with_bundle SHALL use import_to_bundle and export_from_bundle internally

#### Scenario: Validation-only module omits IO operations

- **WHEN** a module only validates bundles without external IO
- **THEN** it MAY implement only validate_bundle
- **AND** SHALL NOT be required to implement import/export/sync operations

### Requirement: ValidationReport model for validate_bundle results

The system SHALL provide a `ValidationReport` Pydantic model for structured validation results.

#### Scenario: ValidationReport has status field

- **WHEN** validate_bundle returns ValidationReport
- **THEN** report MUST have `status` field with values: "passed", "failed", "warnings"

#### Scenario: ValidationReport has violations list

- **WHEN** validation finds issues
- **THEN** report MUST have `violations` list of dicts with keys: severity, message, location

#### Scenario: ValidationReport has summary field

- **WHEN** validation completes
- **THEN** report MUST have `summary` field with counts: total_checks, passed, failed, warnings

### Requirement: Requirements Module IO Contract

Requirements implementations SHALL consume core requirements context adapter
helpers through the existing `ModuleIOContract` boundary.

#### Scenario: Import operation maps backlog items to requirements

- **GIVEN** source-attributed requirement records imported by a module
- **WHEN** `import_to_bundle` stores normalized requirements on a `ProjectBundle`
- **THEN** requirements are added under the `requirements.inputs` extension with stable IDs
- **AND** parse diagnostics remain available to the module runtime for partial failures.

#### Scenario: Validate operation enforces profile schema

- **GIVEN** a requirements bundle and active validation profile
- **WHEN** `validate_bundle` delegates to core requirements context validation
- **THEN** missing evidence links and weak context are reported
- **AND** validation severity respects the selected evidence strictness profile.

#### Scenario: Requirements runtime mounts through grouped module metadata

- **GIVEN** a paired requirements runtime package with category `requirements`
- **WHEN** module metadata is discovered by core registry validation
- **THEN** the `requirements` category is accepted with group command `requirements`
- **AND** root CLI command handlers remain owned by the paired requirements runtime.

#### Scenario: Installed requirements runtime is discoverable through grouped metadata

- **GIVEN** the paired requirements runtime package is installed and enabled
- **AND** the package exposes a native `requirements` command app
- **WHEN** core registry validation processes the discovered metadata
- **THEN** the runtime remains available to the module command host
- **AND** root CLI handlers and recovery UX remain owned by the paired requirements runtime.
