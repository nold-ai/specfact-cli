# Implementation Tasks: Implement OpenSpec Bridge Adapter

## Prerequisites

- [x] **Dependency Check**: Verify `add-change-tracking-datamodel` change is implemented
  - [x] Change tracking models (`ChangeProposal`, `FeatureDelta`, etc.) exist
  - [x] `BundleManifest` and `ProjectBundle` extended with change tracking
  - [x] Schema v1.1 support is available

## 1. Extend Bridge Configuration Model

- [x] 1.1 Add OpenSpec adapter type (`src/specfact_cli/models/bridge.py`)
  - [x] 1.1.1 Add `OPENSPEC = "openspec"` to `AdapterType` enum
  - [x] 1.1.2 Update enum docstring to include OpenSpec

- [x] 1.2 Add OpenSpec preset configuration (`src/specfact_cli/models/bridge.py`)
  - [x] 1.2.1 Add `preset_openspec()` classmethod to `BridgeConfig`
  - [x] 1.2.2 Define artifact mappings:
    - `specification`: `openspec/specs/{feature_id}/spec.md`
    - `project_context`: `openspec/project.md`
    - `change_proposal`: `openspec/changes/{change_name}/proposal.md`
    - `change_tasks`: `openspec/changes/{change_name}/tasks.md`
    - `change_spec_delta`: `openspec/changes/{change_name}/specs/{feature_id}/spec.md`
  - [x] 1.2.3 Add type hints and docstrings
  - [x] 1.2.4 Add contract decorators (@beartype, @ensure)

- [x] 1.3 Add cross-repository support (`src/specfact_cli/models/bridge.py`)
  - [x] 1.3.1 Add `external_base_path: Path | None` field to `BridgeConfig`
  - [x] 1.3.2 Add field description explaining cross-repo usage
  - [x] 1.3.3 Ensure backward compatibility (default None)
  - [x] 1.3.4 Run `hatch run format` and `hatch run lint` after completion

## 2. Extend BridgeAdapter Interface

- [x] 2.1 Add `get_capabilities()` method to BridgeAdapter interface (`src/specfact_cli/adapters/base.py`)
  - [x] 2.1.1 Add abstract method signature: `get_capabilities(repo_path: Path, bridge_config: BridgeConfig | None = None) -> ToolCapabilities`
  - [x] 2.1.2 Add docstring explaining purpose (returns tool capabilities for detected repository)
  - [x] 2.1.3 Add contract decorators (@beartype, @require, @ensure)
  - [x] 2.1.4 Update existing adapters to implement this method
    - [x] 2.1.4.1 Implement in `GitHubAdapter`
    - [x] 2.1.4.2 Implement in `OpenSpecAdapter` (in section 4)

## 3. Refactor Bridge Probe to Use Adapter Registry (CRITICAL - Universal Abstraction Layer)

**⚠️ IMPORTANT**: This refactoring is required for universal abstraction layer compliance. Do NOT add hard-coded detection methods.

- [x] 3.1 Remove hard-coded detection methods (`src/specfact_cli/sync/bridge_probe.py`)
  - [x] 3.1.1 **DO NOT add `_is_openspec_repo()` or `_detect_openspec()` methods**
  - [x] 3.1.2 Remove `_is_speckit_repo()` method (will move to SpecKitAdapter in future)
  - [x] 3.1.3 Remove `_detect_speckit()` method (will move to SpecKitAdapter in future)
  - [x] 3.1.4 Document that detection logic belongs in adapter modules, not BridgeProbe

- [x] 3.2 Refactor `detect()` method to use adapter registry
  - [x] 3.2.1 Import `AdapterRegistry` from `specfact_cli.adapters.registry`
  - [x] 3.2.2 Loop through all registered adapters: `for adapter_type, adapter_class in AdapterRegistry._adapters.items()`
  - [x] 3.2.3 Create adapter instance: `adapter = adapter_class()`
  - [x] 3.2.4 Call `adapter.detect(self.repo_path, bridge_config)` for each adapter
  - [x] 3.2.5 When adapter detects, call `adapter.get_capabilities(self.repo_path, bridge_config)`
  - [x] 3.2.6 Return `ToolCapabilities` from first adapter that detects
  - [x] 3.2.7 Remove all hard-coded adapter checks (if/elif chains)
  - [x] 3.2.8 Add contract decorators and error handling

- [x] 3.3 Refactor `auto_generate_bridge()` to use adapter registry
  - [x] 3.3.1 Import `AdapterRegistry`
  - [x] 3.3.2 If `capabilities.tool != "unknown"`, use `AdapterRegistry.get_adapter(capabilities.tool)`
  - [x] 3.3.3 Call `adapter.generate_bridge_config(self.repo_path)` instead of hard-coded checks
  - [x] 3.3.4 Remove all hard-coded adapter checks (if/elif chains)
  - [x] 3.3.5 Fall back to generic markdown bridge if no adapter found

- [x] 3.4 Update method signatures to accept bridge_config
  - [x] 3.4.1 Update `detect(bridge_config: BridgeConfig | None = None)` signature
  - [x] 3.4.2 Pass bridge_config to adapter.detect() calls
  - [x] 3.4.3 Pass bridge_config to adapter.get_capabilities() calls

- [x] 3.5 Run quality checks
  - [x] 3.5.1 Run `hatch run format`
  - [x] 3.5.2 Run `hatch run lint`
  - [x] 3.5.3 Run `hatch run type-check`
  - [x] 3.5.4 Fix any issues
  - [x] 3.5.5 Verify no hard-coded adapter checks remain

## 4. Create OpenSpec Parser

- [x] 4.1 Create parser module (`src/specfact_cli/adapters/openspec_parser.py` or inline in openspec.py)
  - [x] 4.1.1 **Decision**: Parser is adapter-specific implementation detail, belongs in adapter module
  - [x] 4.1.2 Create `OpenSpecParser` class (can be private class or separate file in adapters/)
  - [x] 4.1.3 Add docstring explaining parser purpose (adapter-specific OpenSpec format parsing)
  - [x] 4.1.4 Add type hints and contract decorators (@beartype, @icontract)
  - [x] 4.1.5 Run `hatch run format` and `hatch run lint` after implementation

- [x] 4.2 Implement project.md parser
  - [x] 4.2.1 Add `parse_project_md(path: Path)` method
  - [x] 4.2.2 Parse markdown sections (Purpose, Tech Stack, Conventions, etc.)
  - [x] 4.2.3 Return structured dict with parsed content
  - [x] 4.2.4 Handle missing file gracefully

- [x] 4.3 Implement spec.md parser
  - [x] 4.3.1 Add `parse_spec_md(path: Path)` method
  - [x] 4.3.2 Parse feature specification markdown
  - [x] 4.3.3 Extract requirements and scenarios
  - [x] 4.3.4 Return structured dict

- [x] 4.4 Implement change proposal parser
  - [x] 4.4.1 Add `parse_change_proposal(path: Path)` method
  - [x] 4.4.2 Parse proposal.md (Why, What Changes, Impact)
  - [x] 4.4.3 Return structured dict

- [x] 4.5 Implement delta spec parser
  - [x] 4.5.1 Add `parse_change_spec_delta(path: Path)` method
  - [x] 4.5.2 Parse ADDED/MODIFIED/REMOVED markers
  - [x] 4.5.3 Extract change type and content
  - [x] 4.5.4 Return structured dict with change metadata

- [x] 4.6 Add utility methods
  - [x] 4.6.1 Add `list_active_changes(repo_path: Path)` method
  - [x] 4.6.2 List all changes in `openspec/changes/`
  - [x] 4.6.3 Support cross-repo paths
  - [x] 4.6.4 Run `hatch run format` and `hatch run lint` after completion

## 5. Create OpenSpec Adapter (Plugin-Based Architecture)

- [x] 5.1 Create adapter module (`src/specfact_cli/adapters/openspec.py`)
  - [x] 5.1.1 Create `OpenSpecAdapter` class extending `BridgeAdapter`
  - [x] 5.1.2 Add docstring explaining adapter purpose
  - [x] 5.1.3 Add type hints and contract decorators to all methods

- [x] 5.2 Implement `detect()` method
  - [x] 5.2.1 Check for `openspec/project.md` and `openspec/specs/` directory
  - [x] 5.2.2 Support cross-repo detection via `bridge_config.external_base_path`
  - [x] 5.2.3 Add contract decorators (@beartype, @require, @ensure)
  - [x] 5.2.4 Return bool indicating OpenSpec detection
  - [x] 5.2.5 **Note**: This method is called by BridgeProbe via adapter registry (no hard-coding)

- [x] 5.3 Implement `get_capabilities()` method
  - [x] 5.3.1 Return `ToolCapabilities` with tool="openspec"
  - [x] 5.3.2 Set `specs_dir = "openspec/specs"`
  - [x] 5.3.3 Check for active changes in `openspec/changes/` (set `has_custom_hooks` flag)
  - [x] 5.3.4 Support cross-repo paths via bridge_config
  - [x] 5.3.5 Add contract decorators

- [x] 5.4 Implement `import_artifact()` method
  - [x] 5.4.1 Use `OpenSpecParser` for parsing based on artifact_key
  - [x] 5.4.2 Map OpenSpec artifacts to SpecFact models (Feature, ChangeProposal, etc.)
  - [x] 5.4.3 Store OpenSpec paths in `source_tracking.source_metadata` with structure:

    ```python
    {
      "openspec_path": "openspec/specs/{feature}/spec.md",
      "openspec_type": "specification|project_context|change_proposal|change_spec_delta",
      "openspec_base_path": "..."  # external_base_path if cross-repo
    }
    ```

  - [x] 5.4.4 Use `load_project_bundle()` from `bundle_loader.py` for loading bundles
  - [x] 5.4.5 Support cross-repo paths via `bridge_config.external_base_path`
  - [x] 5.4.6 Add contract decorators and error handling

- [x] 5.5 Implement `export_artifact()` method (stub for Phase 1 - read-only)
  - [x] 5.5.1 Add stub implementation (Phase 1 is read-only)
  - [x] 5.5.2 Add contract decorators
  - [x] 5.5.3 Raise NotImplementedError with message about Phase 1 limitation

- [x] 5.6 Implement `generate_bridge_config()` method
  - [x] 5.6.1 Return `BridgeConfig.preset_openspec()`
  - [x] 5.6.2 Include `external_base_path` if cross-repo detected
  - [x] 5.6.3 Add contract decorators

- [x] 5.7 Implement `load_change_tracking()` method
  - [x] 5.7.1 Check `bridge_config.external_base_path` for cross-repo support
  - [x] 5.7.2 Load change tracking from OpenSpec changes directory
  - [x] 5.7.3 Parse active changes and map to `ChangeTracking` model
  - [x] 5.7.4 Use `load_project_bundle()` for consistency
  - [x] 5.7.5 Add contract decorators and error handling

- [x] 5.8 Implement `save_change_tracking()` method (stub for Phase 1 - read-only)
  - [x] 5.8.1 Add stub implementation (Phase 1 is read-only)
  - [x] 5.8.2 Add contract decorators
  - [x] 5.8.3 Raise NotImplementedError with message about Phase 1 limitation

- [x] 5.9 Implement `load_change_proposal()` method
  - [x] 5.9.1 Check `bridge_config.external_base_path` for cross-repo support
  - [x] 5.9.2 Load proposal from `openspec/changes/{change_name}/proposal.md`
  - [x] 5.9.3 Use `OpenSpecParser.parse_change_proposal()` for parsing
  - [x] 5.9.4 Map to `ChangeProposal` model
  - [x] 5.9.5 Add contract decorators and error handling

- [x] 5.10 Implement `save_change_proposal()` method (stub for Phase 1 - read-only)
  - [x] 5.10.1 Add stub implementation (Phase 1 is read-only)
  - [x] 5.10.2 Add contract decorators
  - [x] 5.10.3 Raise NotImplementedError with message about Phase 1 limitation

- [x] 5.11 Register adapter in registry
  - [x] 5.11.1 Update `src/specfact_cli/adapters/__init__.py`
  - [x] 5.11.2 Import `OpenSpecAdapter`
  - [x] 5.11.3 Call `AdapterRegistry.register("openspec", OpenSpecAdapter)`
  - [x] 5.11.4 Ensure registration happens at module import time

- [x] 5.12 Run quality checks
  - [x] 5.12.1 Run `hatch run format`
  - [x] 5.12.2 Run `hatch run lint`
  - [x] 5.12.3 Run `hatch run type-check`
  - [x] 5.12.4 Fix any issues

## 6. Refactor Bridge Sync to Use Adapter Registry (CRITICAL - Universal Abstraction Layer)

**⚠️ IMPORTANT**: This refactoring is required for universal abstraction layer compliance. Do NOT add hard-coded adapter methods.

- [x] 6.1 Remove hard-coded adapter checks from `import_artifact()` (`src/specfact_cli/sync/bridge_sync.py`)
  - [x] 6.1.1 **DO NOT add `_import_openspec_artifact()` method**
  - [x] 6.1.2 Remove existing `if self.bridge_config.adapter == AdapterType.SPECKIT:` check (line 180)
  - [x] 6.1.3 Remove `_import_speckit_artifact()` method (will move to SpecKitAdapter in future)
  - [x] 6.1.4 Remove `_import_generic_markdown()` method (will move to GenericMarkdownAdapter in future)
  - [x] 6.1.5 Document that adapter-specific logic belongs in adapter modules, not BridgeSync

- [x] 6.2 Refactor `import_artifact()` to use adapter registry
  - [x] 6.2.1 Import `AdapterRegistry` from `specfact_cli.adapters.registry`
  - [x] 6.2.2 Get adapter via `AdapterRegistry.get_adapter(self.bridge_config.adapter.value)`
  - [x] 6.2.3 Call `adapter.import_artifact(artifact_key, artifact_path, project_bundle, bridge_config)`
  - [x] 6.2.4 Remove all hard-coded adapter routing (if/elif chains)
  - [x] 6.2.5 Ensure bridge_config is passed to adapter methods
  - [x] 6.2.6 Add consistent error handling with user-friendly messages
  - [x] 6.2.7 Add Rich Progress display for long-running operations

- [x] 6.3 Refactor `export_artifact()` similarly
  - [x] 6.3.1 Remove hard-coded adapter checks
  - [x] 6.3.2 Use adapter registry
  - [x] 6.3.3 Call `adapter.export_artifact()` with bridge_config parameter
  - [x] 6.3.4 Remove all hard-coded adapter routing

- [x] 6.4 Prepare for future adapter creation (optional but recommended)
  - [x] 6.4.1 Document that SpecKitAdapter should be created to move Spec-Kit logic
  - [x] 6.4.2 Document that GenericMarkdownAdapter should be created to move generic logic
  - [x] 6.4.3 Note: These can be created in separate changes, but prepare structure now

- [x] 6.5 Add alignment report generation
  - [x] 6.5.1 Create `generate_alignment_report()` method in `bridge_sync.py`
  - [x] 6.5.2 Compare SpecFact features vs OpenSpec specs
  - [x] 6.5.3 Identify gaps (OpenSpec specs not in SpecFact)
  - [x] 6.5.4 Calculate coverage percentage
  - [x] 6.5.5 Generate Rich-formatted report with findings (tables, progress bars)
  - [x] 6.5.6 Output report to console and optionally save to file
  - [x] 6.5.7 Use Rich console for consistent UI/UX with other commands

- [x] 6.6 Run quality checks
  - [x] 6.6.1 Run `hatch run format`
  - [x] 6.6.2 Run `hatch run lint`
  - [x] 6.6.3 Run `hatch run type-check`
  - [x] 6.6.4 Fix any issues
  - [x] 6.6.5 Verify no hard-coded adapter checks remain

## 7. Extend CLI Command

- [x] 7.1 Update sync bridge command (`src/specfact_cli/commands/sync.py`)
  - [x] 7.1.1 Add "openspec" to supported adapters list in help text
  - [x] 7.1.2 Update help text to include OpenSpec examples
  - [x] 7.1.3 Update adapter validation to accept OpenSpec (use AdapterRegistry.is_registered())
  - [x] 7.1.4 Use adapter registry pattern (no hard-coded adapter checks)
  - [x] 7.1.5 Add Rich progress display for sync operations (consistent with existing commands)
  - [x] 7.1.6 Add consistent error handling with user-friendly messages
  - [x] 7.1.7 Support `--external-base-path` option for cross-repo OpenSpec
  - [x] 7.1.8 Update command docstring with OpenSpec examples

- [x] 7.2 Add OpenSpec-specific options
  - [x] 7.2.1 Add `--external-base-path` option for cross-repo
  - [x] 7.2.2 Pass `external_base_path` to bridge config when provided
  - [x] 7.2.3 Update command docstring with cross-repo examples
  - [x] 7.2.4 Add validation for external_base_path (must exist, must be directory)

- [x] 7.3 Run quality checks
  - [x] 7.3.1 Run `hatch run format`
  - [x] 7.3.2 Run `hatch run lint`
  - [x] 7.3.3 Run `hatch run type-check`
  - [x] 7.3.4 Fix any issues

## 8. Testing

- [x] 8.1 Unit tests for bridge model (`tests/unit/models/test_bridge.py`)
  - [x] 8.1.1 Test `AdapterType.OPENSPEC` enum value
  - [x] 8.1.2 Test `preset_openspec()` method
  - [x] 8.1.3 Test `external_base_path` field

- [x] 8.2 Unit tests for bridge probe (`tests/unit/sync/test_bridge_probe.py`)
  - [x] 8.2.1 Test `detect()` uses adapter registry (no hard-coded checks)
  - [x] 8.2.2 Test `detect()` with OpenSpec adapter (via registry)
  - [x] 8.2.3 Test `detect()` with cross-repo OpenSpec (via bridge_config)
  - [x] 8.2.4 Test `auto_generate_bridge()` uses adapter registry
  - [x] 8.2.5 Test `auto_generate_bridge()` for OpenSpec (via registry)
  - [x] 8.2.6 Verify no hard-coded adapter checks in BridgeProbe

- [x] 8.3 Unit tests for OpenSpec parser (`tests/unit/adapters/test_openspec_parser.py` or `test_openspec.py`)
  - [x] 8.3.1 Test `parse_project_md()` with valid file
  - [x] 8.3.2 Test `parse_project_md()` with missing file
  - [x] 8.3.3 Test `parse_spec_md()` with valid spec
  - [x] 8.3.4 Test `parse_change_proposal()` with valid proposal
  - [x] 8.3.5 Test `parse_change_spec_delta()` with ADDED/MODIFIED/REMOVED
  - [x] 8.3.6 Test `list_active_changes()` method
  - [x] 8.3.7 Test cross-repo path resolution

- [x] 8.4 Unit tests for OpenSpec adapter (`tests/unit/adapters/test_openspec.py`)
  - [x] 8.4.1 Test `detect()` method (same-repo)
  - [x] 8.4.2 Test `detect()` method (cross-repo)
  - [x] 8.4.3 Test `get_capabilities()` method
  - [x] 8.4.4 Test `import_artifact()` for each artifact type
  - [x] 8.4.5 Test `export_artifact()` raises NotImplementedError (Phase 1)
  - [x] 8.4.6 Test `generate_bridge_config()` method
  - [x] 8.4.7 Test `load_change_tracking()` method
  - [x] 8.4.8 Test `save_change_tracking()` raises NotImplementedError (Phase 1)
  - [x] 8.4.9 Test `load_change_proposal()` method
  - [x] 8.4.10 Test `save_change_proposal()` raises NotImplementedError (Phase 1)
  - [x] 8.4.11 Test source_tracking metadata structure
  - [x] 8.4.12 Test cross-repo path resolution
  - [x] 8.4.13 Test adapter registry registration

- [x] 8.5 Unit tests for bridge sync (`tests/unit/sync/test_bridge_sync.py`)
  - [x] 8.5.1 Test `import_artifact()` uses adapter registry (no hard-coding)
  - [x] 8.5.2 Test alignment report generation
  - [x] 8.5.3 Test cross-repo path resolution
  - [x] 8.5.4 Test error handling and user-friendly messages
  - [x] 8.5.5 Test Rich progress display integration
  - [x] 8.5.6 Verify no hard-coded adapter checks remain

- [x] 8.6 Integration tests (`tests/integration/sync/test_openspec_bridge_sync.py`)
  - [x] 8.6.1 Test end-to-end read-only sync
  - [x] 8.6.2 Test with same-repo OpenSpec
  - [x] 8.6.3 Test with cross-repo OpenSpec
  - [x] 8.6.4 Test alignment report output
  - [x] 8.6.5 Test CLI command execution
  - [x] 8.6.6 Test OpenSpec repository detection
  - [x] 8.6.7 Test project context import from OpenSpec
  - [x] 8.6.8 Test specification import from OpenSpec
  - [x] 8.6.9 Test change tracking loading from OpenSpec
  - [x] 8.6.10 Test adapter registry integration
  - [x] 8.6.11 Test error handling for missing OpenSpec structure
  - [x] 8.6.12 Test read-only mode enforcement

- [x] 8.7 End-to-end (E2E) tests (`tests/e2e/test_openspec_bridge_workflow.py`)
  - [x] 8.7.1 Test complete OpenSpec → SpecFact workflow
  - [x] 8.7.2 Test OpenSpec sync with existing bundle
  - [x] 8.7.3 Test OpenSpec change tracking workflow
  - [x] 8.7.4 Test OpenSpec alignment report workflow
  - [x] 8.7.5 Test OpenSpec cross-repo workflow
  - [x] 8.7.6 Test OpenSpec source tracking metadata

## 9. Documentation

- [x] 9.1 Update architecture documentation
  - [x] 9.1.1 Document OpenSpec adapter in bridge pattern docs
  - [x] 9.1.2 Document cross-repository support
  - [x] 9.1.3 Document plugin-based adapter architecture
  - [x] 9.1.4 Document refactoring of BridgeProbe and BridgeSync to use adapter registry

- [x] 9.2 Update CLI command documentation
  - [x] 9.2.1 Add OpenSpec examples to sync command docs
  - [x] 9.2.2 Document cross-repo configuration
  - [x] 9.2.3 Document `--external-base-path` option

- [x] 9.3 Update CHANGELOG.md
  - [x] 9.3.1 Add entry for OpenSpec bridge adapter
  - [x] 9.3.2 Note Phase 1 (read-only sync) completion
  - [x] 9.3.3 Note plugin-based adapter architecture
  - [x] 9.3.4 Note refactoring of BridgeProbe and BridgeSync for universal abstraction layer

## 10. Validation

- [x] 10.1 Run full test suite
  - [x] 10.1.1 Ensure all existing tests pass
  - [x] 10.1.2 Ensure new tests pass
  - [x] 10.1.3 Verify 80%+ coverage maintained
  - [x] 10.1.4 Run `hatch run smart-test` or `hatch test --cover -v`

- [x] 10.2 Run linting and formatting
  - [x] 10.2.1 Run `hatch run format`
  - [x] 10.2.2 Run `hatch run lint`
  - [x] 10.2.3 Run `hatch run type-check`
  - [x] 10.2.4 Fix any issues
  - [x] 10.2.5 Verify no linter errors or warnings

- [x] 10.3 Verify universal abstraction layer compliance
  - [x] 10.3.1 Verify no hard-coded adapter checks in BridgeProbe
  - [x] 10.3.2 Verify no hard-coded adapter checks in BridgeSync
  - [x] 10.3.3 Verify all adapters registered in AdapterRegistry
  - [x] 10.3.4 Verify all adapters implement BridgeAdapter interface completely
  - [x] 10.3.5 Verify change tracking accessed via adapter interface only
  - [x] 10.3.6 Verify no hard-coded paths in core models

- [x] 10.4 Manual testing
  - [x] 10.4.1 Test with same-repo OpenSpec (tested with `/tmp/test-openspec-repo` - command executed successfully)
  - [x] 10.4.2 Test with cross-repo OpenSpec (specfact-cli-internal) (tested with `--external-base-path ../specfact-cli-internal` - command executed successfully)
  - [x] 10.4.3 Verify alignment report generation (tested - alignment report generation attempted when bundle exists, shows appropriate message)
  - [x] 10.4.4 Verify CLI command works (tested - `specfact sync bridge --adapter openspec --mode read-only` works correctly)
  - [x] 10.4.5 Verify Rich progress display works (tested - shows spinner `⠋` and progress messages like "✓ Import complete")
  - [x] 10.4.6 Verify error handling provides user-friendly messages (tested - shows clear errors: "Invalid value for '--repo': Directory does not exist", "Unsupported adapter: invalid-adapter", "Export-only mode requires DevOps adapter")

  **Note**: Manual testing completed successfully. All CLI commands work as expected with proper error handling and Rich progress display.
