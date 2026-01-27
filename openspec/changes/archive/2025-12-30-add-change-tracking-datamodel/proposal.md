# Change: Add Change Tracking Data Model

**Status**: applied

## Why

SpecFact CLI currently lacks explicit change tracking capabilities (ADDED/MODIFIED/REMOVED delta tracking) required for OpenSpec integration. OpenSpec uses delta specs to track proposed changes before they become source-of-truth, which requires data models to represent:

- Change proposals (what, why, when, who)
- Feature deltas (ADDED/MODIFIED/REMOVED changes)
- Change tracking (active proposals and deltas)
- Change archives (completed changes with audit trail)

This change implements the underlying data model foundation (Phase 2) before connecting the OpenSpec bridge adapter. The models are **tool-agnostic** and accessed via bridge adapters, ensuring extensibility for future tools (Linear, Jira, etc.) that may support similar change tracking.

## What Changes

- **NEW**: `src/specfact_cli/models/change.py` - Tool-agnostic change tracking models
  - `ChangeType` enum (ADDED, MODIFIED, REMOVED)
  - `FeatureDelta` model (delta tracking for feature changes)
  - `ChangeProposal` model (change proposals with metadata)
  - `ChangeTracking` model (active changes tracking)
  - `ChangeArchive` model (completed changes archive)

- **EXTEND**: `src/specfact_cli/models/project.py`
  - `BundleManifest` adds optional `change_tracking` and `change_archive` fields (v1.1)
  - `ProjectBundle` adds optional `change_tracking` field and helper methods

- **EXTEND**: Schema versioning
  - Schema v1.0 → v1.1 (backward compatible, all new fields optional)
  - Migration path for existing bundles

- **DESIGN**: Tool-agnostic architecture
  - All change tracking accessed via bridge adapters (no hard-coded paths)
  - Tool-specific metadata stored in `source_tracking`, not model fields
  - Adapter interface for loading/saving change tracking

## Impact

- **Affected specs**: None (new capability)
- **Affected code**:
  - `src/specfact_cli/models/change.py` (NEW)
  - `src/specfact_cli/models/project.py` (EXTEND)
  - `src/specfact_cli/models/__init__.py` (EXPORT new models)
  - Bundle loading/saving logic (EXTEND for v1.1 support)
  - Schema migration utilities (NEW)

- **Breaking changes**: None (backward compatible)
- **Dependencies**:
  - Requires `SourceTracking` model (already exists)
  - Requires bridge adapter architecture (already exists)
  - Foundation for OpenSpec bridge adapter (Phase 1.5)

## Alignment with Implementation Plans

### Bridge Adapter Data Model Plan

- ✅ **Tool-Agnostic Models**: All change tracking models are adapter-agnostic
- ✅ **Source Tracking**: Tool-specific metadata stored in `source_tracking`, not model fields
- ✅ **Adapter Interface**: Change tracking accessed via bridge adapters (no hard-coded paths)
- ✅ **Cross-Repository Support**: Adapters support `external_base_path` for cross-repo configurations

### OpenSpec Data Model Plan

- ✅ **Model Structure**: Matches required models from OPENSPEC_DATA_MODEL_PLAN.md
- ✅ **Schema Versioning**: v1.0 → v1.1 backward compatible extension
- ✅ **Adapter Pattern**: Follows adapter-based access pattern from plan
- ✅ **Validation Fields**: Includes `validation_status` and `validation_results` in `FeatureDelta`

### SpecFact 0.x to 1.x Bridge Plan

- ✅ **Phase 2 Timing**: Aligns with v0.22.0 - v0.23.0 timeline
- ✅ **No Breaking Changes**: Maintains backward compatibility
- ✅ **Foundation**: Provides foundation for OpenSpec bridge adapter

### Ultimate Vision v1.0

- ✅ **V-1 Gap Discovery**: Change proposals identify gaps before they become issues
- ✅ **V-2 Quality Scoring**: Change archives provide audit trail for quality metrics
- ✅ **Bridge Architecture**: Enables OpenSpec integration for brownfield modernization
- ✅ **Tool-Agnostic**: Supports future tools (Linear, Jira) using same models

---

## Implementation Status

**Status**: ✅ **COMPLETE** (v0.21.1, 2025-12-30)

### Completed Implementation

**Data Models** (✅ Complete):

- ✅ Created `src/specfact_cli/models/change.py` with all 5 tool-agnostic models
- ✅ Extended `BundleManifest` with optional `change_tracking` and `change_archive` fields
- ✅ Extended `ProjectBundle` with optional `change_tracking` field
- ✅ Added helper methods: `get_active_changes()`, `get_feature_deltas()`, `_is_schema_v1_1()`
- ✅ Schema version v1.1 support with backward compatibility for v1.0 bundles

**Bridge Adapter Interface** (✅ Complete):

- ✅ Extended `BridgeAdapter` interface with 4 new abstract methods:
  - `load_change_tracking()` - Load change tracking from adapter-specific storage
  - `save_change_tracking()` - Save change tracking to adapter-specific storage
  - `load_change_proposal()` - Load individual change proposal
  - `save_change_proposal()` - Save individual change proposal
- ✅ Updated `GitHubAdapter` to implement new interface methods (export-only adapter)

**Testing** (✅ Complete):

- ✅ Created comprehensive unit tests (`tests/unit/models/test_change.py`) - 27 tests passing
- ✅ Extended existing tests (`tests/unit/models/test_project.py`) with change tracking coverage
- ✅ Verified backward compatibility (v1.0 bundles load correctly)
- ✅ All tests passing with ≥80% coverage

**Documentation** (✅ Complete):

- ✅ Added Change Tracking Models section to `docs/reference/architecture.md`
- ✅ Added Bridge Adapter Interface section to `docs/reference/architecture.md`
- ✅ Created `docs/reference/schema-versioning.md` reference document
- ✅ Updated `docs/reference/directory-structure.md` with schema versioning notes
- ✅ Updated CHANGELOG.md (v0.21.1)

**Implementation Plans** (✅ Complete):

- ✅ Updated `OPENSPEC_DATA_MODEL_PLAN.md` - Phase 2 marked complete
- ✅ Updated `BRIDGE_ADAPTER_DATA_MODEL_PLAN.md` - Phase 2 marked complete
- ✅ Updated `OPENSPEC_INTEGRATION_PLAN.md` - Phase 0 (foundation) marked complete

### Implementation Summary

**Files Created**:

- `src/specfact_cli/models/change.py` (119 lines) - All change tracking models
- `tests/unit/models/test_change.py` (461 lines) - Comprehensive unit tests
- `docs/reference/schema-versioning.md` (179 lines) - Schema versioning reference

**Files Modified**:

- `src/specfact_cli/models/project.py` - Extended with change tracking fields and helper methods
- `src/specfact_cli/models/__init__.py` - Exported new models
- `src/specfact_cli/adapters/base.py` - Extended BridgeAdapter interface
- `src/specfact_cli/adapters/github.py` - Implemented new interface methods
- `docs/reference/architecture.md` - Added change tracking and adapter documentation
- `docs/reference/directory-structure.md` - Added schema versioning notes
- `CHANGELOG.md` - Added v0.21.1 entry
- Version files: `pyproject.toml`, `setup.py`, `src/__init__.py`, `src/specfact_cli/__init__.py` (v0.21.0 → v0.21.1)

**Test Coverage**:

- 27 new unit tests for change tracking models
- Extended tests for ProjectBundle and BundleManifest
- All tests passing, ≥80% coverage maintained

**Next Steps** (Phase 2 - OpenSpec Adapter):

- ⏳ Implement `OpenSpecAdapter` with change tracking methods
- ⏳ Integration tests for OpenSpec sync
- ⏳ End-to-end workflow validation

---

## Source Tracking

### Repository: nold-ai/specfact-cli

- **GitHub Issue**: #64
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/64>
- **Last Synced Status**: applied
- **Sanitized**: true
