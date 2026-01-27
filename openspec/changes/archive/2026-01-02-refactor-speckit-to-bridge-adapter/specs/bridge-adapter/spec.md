## ADDED Requirements

### Requirement: Universal Abstraction Layer for Bridge Adapters

The system SHALL use a plugin-based adapter registry pattern for all tool integrations, with no hard-coded adapter checks in core sync/probe logic.

#### Scenario: Spec-Kit Adapter Registration

- **GIVEN** the bridge adapter architecture
- **WHEN** Spec-Kit adapter is implemented
- **THEN** `SpecKitAdapter` class implements `BridgeAdapter` interface
- **AND** adapter is registered via `AdapterRegistry.register("speckit", SpecKitAdapter)`
- **AND** adapter is accessible via `AdapterRegistry.get_adapter("speckit")`
- **AND** all Spec-Kit logic is encapsulated in `SpecKitAdapter` class

#### Scenario: Adapter-Agnostic Sync Command

- **GIVEN** the `specfact sync bridge` command
- **WHEN** sync command executes for any adapter
- **THEN** uses `AdapterRegistry.get_adapter()` to retrieve adapter
- **AND** uses `BridgeSync` class for sync operations
- **AND** contains no hard-coded `if adapter_type == AdapterType.SPECKIT:` checks
- **AND** contains no direct instantiation of adapter-specific classes (SpecKitSync, SpecKitConverter, SpecKitScanner)

#### Scenario: Adapter-Agnostic Bridge Probe

- **GIVEN** the `BridgeProbe` class
- **WHEN** bridge validation is performed
- **THEN** `validate_bridge()` method contains no hard-coded adapter checks
- **AND** adapter-specific validation suggestions are provided by adapters themselves
- **AND** probe uses adapter registry for all adapter operations

#### Scenario: Adapter-Agnostic Bridge Sync

- **GIVEN** the `BridgeSync` class
- **WHEN** alignment report or other adapter-specific operations are performed
- **THEN** contains no hard-coded adapter value checks (e.g., `adapter.value != "openspec"`)
- **AND** adapter-specific operations are handled via adapter interface methods
- **AND** sync uses adapter registry for all adapter operations
- **AND** adapter-specific kwargs are determined via adapter capabilities, not hard-coded checks

#### Scenario: Adapter-Agnostic Import Command

- **GIVEN** the `specfact import from-bridge` command
- **WHEN** import command executes for any adapter
- **THEN** uses `AdapterRegistry.get_adapter()` to retrieve adapter
- **AND** uses `BridgeSync` class for import operations
- **AND** contains no hard-coded `if adapter_type == AdapterType.SPECKIT:` checks
- **AND** contains no direct instantiation of adapter-specific classes (SpecKitScanner, SpecKitConverter)
- **AND** uses adapter's `detect()` method instead of tool-specific detection methods

#### Scenario: Adapter-Agnostic Sync Mode Detection

- **GIVEN** the `specfact sync bridge` command
- **WHEN** sync mode is auto-detected
- **THEN** uses adapter's `get_capabilities()` to determine supported sync modes
- **AND** contains no hard-coded adapter type lists (e.g., `devops_adapters = ("github", "ado", "linear", "jira")`)
- **AND** contains no hard-coded mode assignments (e.g., `elif adapter_value == "openspec": sync_mode = "read-only"`)
- **AND** sync mode is determined by adapter capabilities, not hard-coded checks

### Requirement: Spec-Kit Adapter Implementation

The system SHALL provide a `SpecKitAdapter` class that encapsulates all Spec-Kit-specific logic.

#### Scenario: Spec-Kit Detection

- **GIVEN** a repository with Spec-Kit structure
- **WHEN** `SpecKitAdapter.detect()` is called
- **THEN** checks for `.specify/` directory (indicates Spec-Kit project)
- **AND** checks for `specs/` directory (classic format) or `docs/specs/` directory (modern format)
- **AND** checks for `.specify/memory/constitution.md` file
- **AND** returns True if Spec-Kit structure is detected (`.specify/` directory exists)
- **AND** supports cross-repo detection via `bridge_config.external_base_path`

#### Scenario: Spec-Kit Capabilities

- **GIVEN** Spec-Kit is detected
- **WHEN** `SpecKitAdapter.get_capabilities()` is called
- **THEN** returns `ToolCapabilities` with:
  - `tool="speckit"`
  - `specs_dir` set to detected format (`specs/` for classic, `docs/specs/` for modern)
  - `has_custom_hooks` flag based on constitution presence and validation (non-minimal constitution)
  - `layout` set to "standard" (Spec-Kit uses standard layout)
- **AND** validates constitution exists and is not minimal (empty or template-only)
- **AND** supports cross-repo paths via bridge_config

#### Scenario: Spec-Kit Artifact Import

- **GIVEN** Spec-Kit artifacts exist in repository
- **WHEN** `SpecKitAdapter.import_artifact()` is called
- **THEN** uses `SpecKitScanner` and `SpecKitConverter` internally
- **AND** maps Spec-Kit artifacts (spec.md, plan.md, tasks.md) to SpecFact models
- **AND** stores Spec-Kit paths in `source_tracking.source_metadata`
- **AND** supports both modern (`.specify/`) and classic (`specs/`) formats

#### Scenario: Spec-Kit Artifact Export

- **GIVEN** SpecFact project bundle with features
- **WHEN** `SpecKitAdapter.export_artifact()` is called
- **THEN** uses `SpecKitConverter.convert_to_speckit()` internally
- **AND** exports SpecFact features to Spec-Kit format (spec.md, plan.md, tasks.md)
- **AND** supports overwrite mode and conflict resolution
- **AND** writes to correct format based on detected Spec-Kit structure

#### Scenario: Spec-Kit Bridge Config Generation

- **GIVEN** Spec-Kit is detected
- **WHEN** `SpecKitAdapter.generate_bridge_config()` is called
- **THEN** returns `BridgeConfig` using existing preset methods:
  - `BridgeConfig.preset_speckit_classic()` if classic format detected (`specs/` directory at root)
  - `BridgeConfig.preset_speckit_modern()` if modern format detected (`docs/specs/` directory)
  - Artifact mappings include: `specification`, `plan`, `tasks`, `contracts`
  - Constitution path: `.specify/memory/constitution.md` (checked for both formats)
- **AND** includes `external_base_path` if cross-repo detected
- **AND** auto-detects format based on directory structure (classic: `specs/` at root, modern: `docs/specs/`)

#### Scenario: Spec-Kit Bidirectional Sync

- **GIVEN** Spec-Kit adapter is used for bidirectional sync
- **WHEN** `BridgeSync.sync_bidirectional()` is called with Spec-Kit adapter
- **THEN** adapter's `import_artifact()` and `export_artifact()` methods handle change detection internally
- **AND** adapter detects changes in Spec-Kit artifacts (via internal `_detect_speckit_changes()` helper)
- **AND** adapter detects changes in SpecFact artifacts (via internal `_detect_specfact_changes()` helper)
- **AND** adapter merges changes and detects conflicts (via internal `_merge_changes()` and `_detect_conflicts()` helpers)
- **AND** conflicts are resolved using priority rules (SpecFact > Spec-Kit for artifacts)

#### Scenario: Spec-Kit Constitution Validation

- **GIVEN** Spec-Kit adapter is used
- **WHEN** `SpecKitAdapter.get_capabilities()` is called
- **THEN** checks for constitution file (`.specify/memory/constitution.md` or classic format)
- **AND** sets `has_custom_hooks` flag based on constitution presence
- **AND** validates constitution is not minimal (if present)
- **AND** returns `ToolCapabilities` with constitution validation status

#### Scenario: Constitution Command Location

- **GIVEN** Spec-Kit constitution management commands exist
- **WHEN** user wants to manage constitution
- **THEN** commands are available via `specfact sdd constitution` (not `specfact bridge constitution`)
- **AND** `specfact bridge` command does not exist (bridge adapters are internal connectors, no user-facing commands)
- **AND** constitution commands (bootstrap, enrich, validate) are under SDD command group (Spec-Kit is an SDD tool)
