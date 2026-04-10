# Technical Design: Change Tracking Data Model

## Context

This design implements the change tracking data model foundation required for OpenSpec integration (Phase 2). The models are **tool-agnostic** and designed for extensibility, allowing future tools (Linear, Jira, etc.) to use the same change tracking capabilities.

## Goals

1. **Tool-Agnostic Models**: Change tracking models work for any tool that supports delta tracking
2. **Backward Compatibility**: Schema v1.0 bundles continue to work (v1.1 is optional extension)
3. **Adapter-Based Access**: All change tracking accessed via bridge adapters (no hard-coded paths)
4. **Extensibility**: Future tools can use same models via `source_tracking` metadata

## Non-Goals

- OpenSpec bridge adapter implementation (separate phase)
- Bidirectional sync logic (separate phase)
- Change proposal UI/workflow (out of scope)

## Decisions

### Decision 1: Tool-Agnostic Models

**What**: Change tracking models (`ChangeProposal`, `FeatureDelta`, etc.) are tool-agnostic.

**Why**:

- OpenSpec is first tool to use them, but Linear/Jira could use them in future
- Avoids hard-coding tool-specific fields in core models
- Enables plugin-based adapter architecture

**Alternatives Considered**:

- OpenSpec-specific models (rejected - not extensible)
- Tool-specific fields in models (rejected - violates adapter pattern)

**Implementation**:

- All tool-specific metadata stored in `source_tracking.source_metadata`
- Adapters handle tool-specific storage locations
- Models remain adapter-agnostic

### Decision 2: Optional Fields (Backward Compatibility)

**What**: All change tracking fields are optional in `BundleManifest` and `ProjectBundle`.

**Why**:

- Existing v1.0 bundles must continue to work
- Change tracking is only needed when using tools that support it
- Gradual adoption path for existing users

**Alternatives Considered**:

- Required fields (rejected - breaks backward compatibility)
- Separate bundle type (rejected - unnecessary complexity)

**Implementation**:

- `change_tracking: ChangeTracking | None = None`
- `change_archive: list[ChangeArchive] = Field(default_factory=list)`
- Schema version check in loading logic

### Decision 3: Adapter-Based Access Pattern

**What**: Change tracking loaded/saved via bridge adapters, not direct file access.

**Why**:

- Adapters decide storage location (OpenSpec uses `openspec/changes/`, others may differ)
- No hard-coded paths in core models
- Supports cross-repository configurations

**Alternatives Considered**:

- Hard-coded paths in core (rejected - not extensible)
- Direct file access (rejected - violates adapter pattern)

**Implementation**:

- Adapter interface methods: `load_change_tracking()`, `save_change_tracking()`, `load_change_proposal()`, `save_change_proposal()`
- Core models don't know about file paths
- Adapters handle OpenSpec-specific paths via `source_tracking`
- **BridgeAdapter Interface Extension**: These methods must be added to `BridgeAdapter` abstract base class
- **Cross-Repository Support**: Adapters must check `bridge_config.external_base_path` before using `bundle_dir`
  - All change tracking paths resolved relative to external base when provided
  - Supports OpenSpec in `specfact-cli-internal` with code in `specfact-cli`
  - Works transparently for both same-repo and cross-repo scenarios

### Decision 4: Schema Version Strategy

**What**: Dual versioning (schema + project) with v1.0 → v1.1 upgrade path.

**Why**:

- Clear migration path for existing bundles
- Backward compatibility guaranteed
- Future-proof for additional extensions

**Alternatives Considered**:

- Breaking change (rejected - breaks existing bundles)
- No versioning (rejected - unclear migration path)

**Implementation**:

- `BundleVersions.schema_version` tracks format version
- Loading logic checks version and handles accordingly
- Optional upgrade utility for v1.0 → v1.1

## Risks / Trade-offs

### Risk 1: Model Complexity

**Risk**: Change tracking models add complexity to core data model.

**Mitigation**:

- All fields optional (backward compatible)
- Clear separation via adapter pattern
- Comprehensive tests

### Risk 2: Adapter Interface Evolution

**Risk**: Adapter interface may need changes as more tools are added.

**Mitigation**:

- Start with minimal interface (load/save change tracking)
- Extend interface as needed (backward compatible additions)
- Document extension points

**Required Interface Extensions**:

The `BridgeAdapter` interface must be extended with the following abstract methods:

```python
@abstractmethod
def load_change_tracking(self, bundle_dir: Path, bridge_config: BridgeConfig | None = None) -> ChangeTracking | None:
    """Load change tracking (adapter-specific storage location)."""
    
@abstractmethod
def save_change_tracking(self, bundle_dir: Path, change_tracking: ChangeTracking, bridge_config: BridgeConfig | None = None) -> None:
    """Save change tracking (adapter-specific storage location)."""
    
@abstractmethod
def load_change_proposal(self, bundle_dir: Path, change_name: str, bridge_config: BridgeConfig | None = None) -> ChangeProposal | None:
    """Load change proposal (adapter-specific storage location)."""
    
@abstractmethod
def save_change_proposal(self, bundle_dir: Path, proposal: ChangeProposal, bridge_config: BridgeConfig | None = None) -> None:
    """Save change proposal (adapter-specific storage location)."""
```

**Cross-Repository Support**:

All adapter methods must support cross-repository configurations:

- Check `bridge_config.external_base_path` before using `bundle_dir`
- Resolve all paths relative to external base when provided
- Support both same-repo (default) and cross-repo scenarios transparently

### Risk 3: Performance Impact

**Risk**: Loading change tracking may slow bundle loading.

**Mitigation**:

- Lazy loading (only load when needed)
- Optional field (skip if not present)
- Cache change tracking in memory

## Migration Plan

### For Existing Bundles (v1.0)

**Automatic**: No migration required - v1.0 bundles load correctly with `change_tracking = None`.

**Optional Upgrade**:

1. Update `bundle.manifest.yaml` schema version to "1.1"
2. Initialize empty `change_tracking` structure (via adapter)
3. Preserve all existing data

### For New Bundles

**Default**: Create with v1.1 schema (includes change tracking structure).

## Open Questions

- Should we add validation rules for change proposals? (e.g., required fields)
- Should we add conflict detection for overlapping changes? (deferred to Phase 3)
- Should we add change proposal approval workflow? (out of scope)

## Implementation Notes

### File Structure

```
src/specfact_cli/models/
├── change.py          # NEW: Change tracking models
├── project.py         # EXTEND: BundleManifest, ProjectBundle
└── __init__.py        # EXTEND: Export change models
```

### Model Relationships

```
ProjectBundle
├── manifest: BundleManifest
│   ├── change_tracking: ChangeTracking | None  # NEW (v1.1)
│   └── change_archive: list[ChangeArchive]      # NEW (v1.1)
└── change_tracking: ChangeTracking | None      # NEW (v1.1)

ChangeTracking
├── proposals: dict[str, ChangeProposal]
└── feature_deltas: dict[str, list[FeatureDelta]]

ChangeProposal
├── name: str
├── status: str (proposed, in-progress, applied, archived)
└── source_tracking: SourceTracking | None  # Tool-specific metadata

FeatureDelta
├── feature_key: str
├── change_type: ChangeType (ADDED, MODIFIED, REMOVED)
├── original_feature: Feature | None
├── proposed_feature: Feature | None
└── source_tracking: SourceTracking | None  # Tool-specific metadata
```

### Tool-Specific Metadata Storage

**Example**: OpenSpec adapter stores OpenSpec paths in `source_tracking`:

```python
change_proposal.source_tracking = SourceTracking(
    source_type="openspec",
    source_id="add-user-feedback",
    source_url="openspec/changes/add-user-feedback/",
    source_metadata={
        "openspec_change_dir": "openspec/changes/add-user-feedback",
        "openspec_proposal_path": "openspec/changes/add-user-feedback/proposal.md"
    }
)
```

**Key Principle**: No hard-coded tool fields in models - all tool-specific data in `source_tracking`.
