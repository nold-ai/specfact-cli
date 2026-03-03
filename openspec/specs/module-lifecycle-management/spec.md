# module-lifecycle-management Specification

## Purpose
TBD - created by archiving change arch-03-module-lifecycle-management. Update Purpose after archive.
## Requirements
### Requirement: Shared helper extraction from cross-module command imports

The system SHALL provide shared bundle conversion and constitution helper utilities under core `specfact_cli.utils` so modules do not import private non-`app` symbols from other modules' `src.commands`.

#### Scenario: Cross-module helper imports use core utility module

**Given** module command implementations that require shared conversion or constitution helper behavior

**When** imports are updated for lifecycle management

**Then** those modules import helpers from `specfact_cli.utils.bundle_converters`

**And** cross-module imports from `specfact_cli.modules.<other>.src.commands` for non-`app` symbols are eliminated

### Requirement: Module manifest core compatibility constraints

The system SHALL support optional `core_compatibility` in each module package manifest using PEP 440 specifier syntax.

#### Scenario: Compatibility field is parsed from module manifest

**Given** a module `module-package.yaml` includes `core_compatibility: ">=0.28.0,<1.0.0"`

**When** package metadata is discovered

**Then** metadata includes the parsed `core_compatibility` string for compatibility evaluation

**And** modules without the field remain valid and are treated as unconstrained

### Requirement: Dependency and compatibility validation during registration

The system SHALL validate dependency availability/enabled state and core compatibility before registering module commands.

#### Scenario: Module with unmet dependency is skipped

**Given** an enabled module declares `module_dependencies` containing a missing or disabled module

**When** command registration runs

**Then** the module is skipped from registration

**And** the reason is emitted to debug logs

#### Scenario: Module with incompatible core constraint is skipped

**Given** an enabled module declares a `core_compatibility` range that does not include the current CLI version

**When** command registration runs

**Then** the module is skipped from registration

**And** debug logs include the module id, required range, and current version

### Requirement: Safe-disable enforcement in init workflow

The system SHALL prevent disabling modules that are required by enabled dependent modules unless the user explicitly forces the action.

#### Scenario: Unsafe disable is blocked without force

**Given** module `A` is enabled and depends on module `B`

**When** the user runs `specfact init --disable-module B`

**Then** the command exits with an error

**And** the error lists enabled dependents that require `B`

**And** the output includes a hint to disable dependents first or use `--force`

#### Scenario: Unsafe disable can be overridden with force

**Given** module `A` is enabled and depends on module `B`

**When** the user runs `specfact init --disable-module B --force`

**Then** module `B` is disabled

**And** enabled dependents of `B` are also disabled transitively

**And** the command proceeds with force-override semantics

#### Scenario: Force enable auto-enables upstream dependencies

**Given** module `A` depends on module `B`

**And** module `B` is currently disabled

**When** the user runs `specfact init --enable-module A --force`

**Then** module `A` is enabled

**And** required upstream dependencies (including `B`) are enabled transitively

### Requirement: Module state visibility and selection UX in init workflow

The system SHALL provide module status visibility and interactive selection ergonomics for enable/disable operations, while preserving explicit module-id requirements in non-interactive mode.

#### Scenario: Installed modules can be listed with enabled/disabled state

**Given** module metadata is discoverable and module state may contain prior enable/disable overrides

**When** the user runs `specfact init --list-modules`

**Then** the command outputs each discovered module with its enabled or disabled status

**And** output reflects the effective merged state from discovered manifests and persisted registry state

#### Scenario: Interactive enable selection uses arrow-key menu

**Given** the terminal is interactive

**And** the user requests module enablement without explicit module ids

**When** the command runs interactive module selection

**Then** the user can pick a module using an up/down selection menu

**And** the selected module is added to the enable list before state persistence

#### Scenario: Interactive disable selection uses arrow-key menu

**Given** the terminal is interactive

**And** the user requests module disablement without explicit module ids

**When** the command runs interactive module selection

**Then** the user can pick a module using an up/down selection menu

**And** the selected module is added to the disable list before safe-disable validation and state persistence

#### Scenario: Non-interactive mode requires explicit module ids

**Given** the command is running in non-interactive mode

**When** the user requests module enablement or disablement without explicit module ids

**Then** the command exits with an error

**And** the error instructs the user to provide `--enable-module <id>` or `--disable-module <id>`

### Requirement: Split bootstrap init from IDE template initialization

The system SHALL separate bootstrap/module lifecycle initialization from IDE prompt/template side effects.

#### Scenario: Top-level init is bootstrap-only

**Given** the user runs `specfact init`

**When** bootstrap and module-state checks complete

**Then** the command does not copy or mutate IDE prompt/template files

**And** it reports prompt installation health with guidance to run `specfact init ide`

#### Scenario: IDE setup is handled by init ide

**Given** the user runs `specfact init ide`

**When** IDE prompt setup executes

**Then** prompt/template files and IDE settings are created or updated for the selected IDE

**And** in interactive mode without `--ide`, IDE selection is provided via up/down selection UI

**And** in non-interactive mode, setup runs directly using explicit `--ide` or auto-detected IDE

### Requirement: Boundary guard for cross-module command imports

The test suite SHALL fail when any module imports non-`app` symbols from another module's `src.commands` package.

#### Scenario: Boundary guard detects cross-module non-app command imports

**Given** a module source file imports a non-`app` symbol from `specfact_cli.modules.<other>.src.commands`

**When** boundary guard tests execute

**Then** tests fail with a clear violation list

**And** guidance points developers to shared utility modules for reusable helpers

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

### Requirement: Lifecycle registration loads module-declared bridges

The system SHALL load and register module-declared service bridges during module lifecycle registration.

#### Scenario: Registration wires declared bridge converters

- **WHEN** `register_module_package_commands()` processes an enabled module with valid `service_bridges`
- **THEN** each declared converter SHALL be registered into `BridgeRegistry`
- **AND** registration SHALL occur without direct core imports from module command internals.

#### Scenario: Bridge registration respects module enable/disable state

- **WHEN** a module is disabled or skipped due to compatibility/dependency failure
- **THEN** its bridge declarations SHALL NOT be registered.

### Requirement: Lifecycle handles bridge conflicts deterministically

The system SHALL handle duplicate bridge IDs predictably and with actionable diagnostics.

#### Scenario: Duplicate bridge ID detected

- **WHEN** two enabled modules declare the same bridge ID
- **THEN** lifecycle registration SHALL apply deterministic conflict handling
- **AND** SHALL log warning/debug details identifying both modules and bridge ID.

### Requirement: Bridge registration failures do not block unrelated modules

The system SHALL degrade gracefully when individual bridge declarations fail.

#### Scenario: Converter import failure is non-fatal

- **WHEN** a module declares a converter class that cannot be imported
- **THEN** lifecycle registration SHALL skip that bridge declaration
- **AND** continue registering other valid modules and bridges.

### Requirement: Lifecycle protocol reporting is accurate and non-duplicative

The system SHALL report ModuleIOContract compliance based on actual module capabilities and avoid duplicate warning emission.

#### Scenario: Compliant module is not misreported as legacy

- **WHEN** lifecycle registration inspects an enabled module that exposes required ModuleIOContract operations
- **THEN** compliance reporting SHALL classify it as full or partial support
- **AND** SHALL NOT classify it as legacy due to inspection-path mismatch.

#### Scenario: Warning output is emitted once per condition

- **WHEN** lifecycle registration logs protocol warnings during startup
- **THEN** each warning condition SHALL be emitted once per module/event
- **AND** a single summary line SHALL report aggregate full/partial/legacy counts.

### Requirement: Registration pipeline SHALL enforce trust checks before enabling modules

The system SHALL execute trust checks before module registration is finalized.

#### Scenario: Trusted module proceeds to registration

- **WHEN** checksum/signature checks pass for a module artifact
- **THEN** registration pipeline SHALL continue and enable module commands.

#### Scenario: Untrusted module is skipped or rejected

- **WHEN** trust checks fail
- **THEN** lifecycle pipeline SHALL skip or reject that module
- **AND** SHALL provide diagnostic logging with failure reason.

### Requirement: Trust failures SHALL not block unrelated module registration

The system SHALL degrade gracefully when one module fails trust checks.

#### Scenario: One module fails, others continue

- **WHEN** one module fails integrity verification during registration
- **THEN** other valid modules SHALL continue registration
- **AND** overall startup SHALL remain operational with warnings.

### Requirement: Registration loads and validates schema extensions

The system SHALL extend module registration to load schema_extensions from manifests, validate namespace uniqueness, and populate the global extension registry.

#### Scenario: Registration loads schema_extensions from manifest
- **WHEN** module registration loads module-package.yaml
- **THEN** system SHALL parse schema_extensions section if present
- **AND** SHALL extract target models, field names, types, descriptions

#### Scenario: Registration validates extension namespace uniqueness
- **WHEN** module declares schema extension with field name
- **THEN** system SHALL check global extension registry for conflicts
- **AND** SHALL reject registration if `module.field` already declared by another module
- **AND** SHALL log error with conflicting module name

#### Scenario: Registration populates global extension registry
- **WHEN** module registration succeeds with schema_extensions
- **THEN** system SHALL add extensions to global registry
- **AND** registry SHALL map module_name → extensions metadata

#### Scenario: Registration logs registered extensions
- **WHEN** module with schema_extensions completes registration
- **THEN** system SHALL log: "Module X registered N schema extensions for [Feature, ProjectBundle]"
- **AND** SHALL log at debug level the specific fields registered

#### Scenario: Registration skips invalid extension declarations
- **WHEN** module declares extension with malformed field name (e.g., contains dots)
- **THEN** system SHALL log warning
- **AND** SHALL skip that extension
- **AND** SHALL NOT fail entire module registration

### Requirement: Registration handles modules from multiple sources

The system SHALL extend registration to handle modules from built-in, marketplace, and custom sources with appropriate lifecycle rules.

#### Scenario: Marketplace modules can be uninstalled
- **WHEN** module from marketplace is registered
- **THEN** system SHALL mark it as uninstallable
- **AND** SHALL allow removal via uninstall command

#### Scenario: Built-in modules cannot be uninstalled
- **WHEN** module from built-in source is registered
- **THEN** system SHALL mark it as non-uninstallable
- **AND** SHALL prevent removal via uninstall command

#### Scenario: Registration validates namespace for marketplace modules
- **WHEN** marketplace module is registered
- **THEN** system SHALL validate id uses "namespace/name" format
- **AND** SHALL log warning if flat name used

### Requirement: Lifecycle command harmonization remains backward compatible

The system SHALL keep existing init-based lifecycle flags functional while introducing `specfact module` as the canonical lifecycle command surface.

#### Scenario: init lifecycle flags remain functional
- **WHEN** user runs `specfact init --list-modules` or `--enable-module/--disable-module`
- **THEN** system SHALL preserve current lifecycle behavior and state updates
- **AND** SHALL provide deprecation guidance toward `specfact module` commands

#### Scenario: module command is canonical lifecycle surface
- **WHEN** user runs `specfact module list` or lifecycle operations
- **THEN** system SHALL provide equivalent lifecycle management capabilities
- **AND** documentation SHALL reference `specfact module` as primary UX

### Requirement: Registration enforces namespace requirements for marketplace modules

The system SHALL validate namespace format during module registration for marketplace-sourced modules.

#### Scenario: Marketplace module must use namespace format
- **WHEN** module from marketplace is registered
- **THEN** id SHALL match format "namespace/name"
- **AND** namespace SHALL be alphanumeric with hyphens
- **AND** name SHALL be alphanumeric with hyphens

#### Scenario: Namespace collision detected
- **WHEN** registering module with id that conflicts with existing module
- **THEN** system SHALL log error "Module namespace collision: {id}"
- **AND** SHALL prevent registration
- **AND** SHALL suggest using alias system for disambiguation

