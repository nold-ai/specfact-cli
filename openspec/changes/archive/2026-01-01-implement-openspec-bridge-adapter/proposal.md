# Change: Implement OpenSpec Bridge Adapter

## Why

SpecFact CLI needs OpenSpec integration to create a complete brownfield legacy modernization stack. OpenSpec provides specification anchoring and delta tracking, while SpecFact provides code2spec extraction, runtime enforcement, and symbolic execution. Together they form a superior brownfield modernization solution.

This change implements Phase 1 (read-only sync) of the OpenSpec integration, enabling SpecFact to validate extracted specs against OpenSpec's source-of-truth specifications. This foundation enables future phases (sidecar integration, bidirectional sync) and establishes the bridge adapter pattern for OpenSpec.

**Dependency**: This change requires the change tracking data model (`add-change-tracking-datamodel`) to be implemented first, as OpenSpec uses delta specs (ADDED/MODIFIED/REMOVED) that require the change tracking models.

## What Changes

- **EXTEND**: `src/specfact_cli/models/bridge.py`
  - Add `OPENSPEC` to `AdapterType` enum
  - Add `preset_openspec()` classmethod to `BridgeConfig`
  - Add `external_base_path` field to `BridgeConfig` (cross-repository support)

- **EXTEND**: `src/specfact_cli/adapters/base.py`
  - Add `get_capabilities()` abstract method to `BridgeAdapter` interface
  - Required for adapter registry pattern in BridgeProbe

- **REFACTOR**: `src/specfact_cli/sync/bridge_probe.py` (CRITICAL - Universal Abstraction Layer)
  - **DO NOT add hard-coded `_is_openspec_repo()` or `_detect_openspec()` methods**
  - Refactor `detect()` method to use adapter registry (loop through registered adapters)
  - Refactor `auto_generate_bridge()` to use adapter registry
  - Remove existing hard-coded Spec-Kit detection methods (move to SpecKitAdapter)
  - This refactoring is required for universal abstraction layer compliance

- **NEW**: `src/specfact_cli/sync/openspec_parser.py`
  - Parse `openspec/project.md` (source-of-truth spec)
  - Parse `openspec/specs/{feature}/spec.md` (current truth)
  - Parse `openspec/changes/{change}/proposal.md` (change proposals)
  - Parse `openspec/changes/{change}/specs/{feature}/spec.md` (delta specs with ADDED/MODIFIED/REMOVED)

- **NEW**: `src/specfact_cli/adapters/openspec.py`
  - Create `OpenSpecAdapter` class implementing `BridgeAdapter` interface
  - Implement all required methods: `detect()`, `import_artifact()`, `export_artifact()`, `generate_bridge_config()`, `load_change_tracking()`, `save_change_tracking()`, `load_change_proposal()`, `save_change_proposal()`
  - Use `OpenSpecParser` for parsing
  - Use `load_project_bundle()` and `save_project_bundle()` from `bundle_loader.py` for consistency
  - Store OpenSpec paths in `source_tracking.source_metadata` with structure: `{"openspec_path": "...", "openspec_type": "specification|project_context|change_proposal|change_spec_delta"}`
  - Support cross-repository paths via `bridge_config.external_base_path`
  - Add contract decorators (`@beartype`, `@icontract`) to all methods
  - Register adapter in `src/specfact_cli/adapters/__init__.py` using `AdapterRegistry.register("openspec", OpenSpecAdapter)`

- **REFACTOR**: `src/specfact_cli/sync/bridge_sync.py` (CRITICAL - Universal Abstraction Layer)
  - **DO NOT add hard-coded `_import_openspec_artifact()` method**
  - Refactor `import_artifact()` to use adapter registry (remove all hard-coded adapter checks)
  - Remove existing `_import_speckit_artifact()` and `_import_generic_markdown()` methods
  - Use `AdapterRegistry.get_adapter()` for all adapters (universal pattern)
  - Generate alignment report (SpecFact vs OpenSpec) using Rich console output
  - Add progress display using Rich Progress for long-running operations
  - This refactoring is required for universal abstraction layer compliance

- **EXTEND**: `src/specfact_cli/commands/sync.py`
  - Update `sync_bridge` command to support OpenSpec adapter
  - Add OpenSpec to supported adapters list
  - Use adapter registry pattern (no hard-coded adapter checks)
  - Add Rich progress display for sync operations
  - Add consistent error handling with user-friendly messages
  - Support `--external-base-path` option for cross-repo OpenSpec

## Impact

- **Affected specs**: None (new capability)
- **Affected code**:
  - `src/specfact_cli/models/bridge.py` (EXTEND)
  - `src/specfact_cli/sync/bridge_probe.py` (EXTEND)
  - `src/specfact_cli/sync/openspec_parser.py` (NEW)
  - `src/specfact_cli/sync/bridge_sync.py` (EXTEND)
  - `src/specfact_cli/commands/sync.py` (EXTEND)
  - Tests for all new/extended components

- **Breaking changes**: None (additive only)
- **Dependencies**:
  - Requires change tracking data model (`add-change-tracking-datamodel`) to be implemented first
  - Uses existing bridge adapter architecture
  - Uses existing `SourceTracking` model

## Success Criteria

- ✅ OpenSpec bridge adapter detects OpenSpec installations (same-repo and cross-repo)
- ✅ OpenSpec parser correctly parses project.md, specs/, and changes/
- ✅ OpenSpecAdapter implements BridgeAdapter interface (plugin-based architecture)
- ✅ Adapter registered in AdapterRegistry
- ✅ Read-only sync generates alignment report (SpecFact vs OpenSpec)
- ✅ CLI command `specfact sync bridge --adapter openspec --mode read-only` works
- ✅ Uses load_project_bundle/save_project_bundle for consistency
- ✅ All methods have contract decorators (@beartype, @icontract)
- ✅ Code passes `hatch run format` and `hatch run lint`
- ✅ Integration tests pass
- ✅ Test coverage ≥80%















---

## Source Tracking

### Repository: nold-ai/specfact-cli

- **GitHub Issue**: #65
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/65>
- **Last Synced Status**: proposed
- **Sanitized**: true
<!-- content_hash: b85eaca51b3716d7 -->