---
layout: default
title: Schema Versioning
permalink: /schema-versioning/
---

# Schema Versioning

This document describes bundle schema versions and backward compatibility in SpecFact CLI.

## Overview

SpecFact CLI uses semantic versioning for bundle schemas to ensure backward compatibility while allowing new features. Bundle schemas are versioned independently from the CLI version.

## Schema Versions

### v1.0 (Original)

**Introduced**: v0.1.0  
**Status**: Stable, fully supported

**Features**:

- Project bundle structure (modular aspect files)
- Feature and story definitions
- Protocol FSM definitions
- Contract definitions
- Basic bundle metadata

**Bundle Manifest**:

```yaml
schema_metadata:
  schema_version: "1.0"
  project_version: "0.1.0"
```

### v1.1 (Change Tracking)

**Introduced**: v0.21.1  
**Status**: Stable, fully supported

**New Features**:

- Change tracking data models (`ChangeTracking`, `ChangeProposal`, `FeatureDelta`, `ChangeArchive`)
- Optional `change_tracking` field in `BundleManifest` and `ProjectBundle`
- Optional `change_archive` field in `BundleManifest`
- Bridge adapter interface extensions for change tracking

**Bundle Manifest**:

```yaml
schema_metadata:
  schema_version: "1.1"
  project_version: "0.1.0"
change_tracking:  # Optional - only present in v1.1+
  proposals:
    add-user-feedback:
      name: "add-user-feedback"
      title: "Add User Feedback Feature"
      # ... change proposal fields
  feature_deltas:
    add-user-feedback:
      - feature_key: "FEATURE-001"
        change_type: "added"
        # ... feature delta fields
change_archive: []  # Optional - only present in v1.1+
```

## Backward Compatibility

### Automatic Compatibility

**v1.0 bundles work with v1.1 CLI**:

- All change tracking fields are optional
- v1.0 bundles load with `change_tracking = None` and `change_archive = []`
- No migration required - bundles continue to work without modification

**v1.1 bundles work with v1.0 CLI** (if CLI supports it):

- Change tracking fields are ignored if CLI doesn't support v1.1
- Core bundle functionality (features, stories, protocols) remains accessible

### Version Detection

The bundle loader automatically detects schema version:

```python
from specfact_cli.models.project import ProjectBundle, _is_schema_v1_1

bundle = ProjectBundle.load_from_directory(bundle_dir)

# Check if bundle uses v1.1 schema
if _is_schema_v1_1(bundle.manifest):
    # Bundle supports change tracking
    if bundle.change_tracking:
        active_changes = bundle.get_active_changes()
        # ... work with change tracking
else:
    # v1.0 bundle - change tracking not available
    # All other functionality works normally
```

### Loading Change Tracking

Change tracking is loaded via bridge adapters (if available):

```python
# In ProjectBundle.load_from_directory()
if _is_schema_v1_1(manifest):
    try:
        adapter = AdapterRegistry.get_adapter(bridge_config.adapter.value)
        change_tracking = adapter.load_change_tracking(bundle_dir, bridge_config)
    except (ImportError, AttributeError, FileNotFoundError):
        # Adapter or change tracking not available - continue without it
        change_tracking = None
```

## Migration

### No Migration Required

**v1.0 → v1.1**: No migration needed - bundles are automatically compatible.

- v1.0 bundles continue to work without modification
- To enable change tracking, update `schema_version` to `"1.1"` in `bundle.manifest.yaml`
- Change tracking will be loaded via adapters when available

### Manual Schema Upgrade (Optional)

If you want to explicitly upgrade a bundle to v1.1:

1. **Update bundle manifest**:

```yaml
# .specfact/projects/<bundle-name>/bundle.manifest.yaml
schema_metadata:
  schema_version: "1.1"  # Changed from "1.0"
  project_version: "0.1.0"
```

1. **Change tracking will be loaded automatically**:

- If bridge adapter is configured, change tracking loads from adapter-specific storage
- If no adapter, `change_tracking` remains `None` (still valid v1.1 bundle)

1. **No data loss**:

- All existing features, stories, and protocols remain unchanged
- Change tracking fields are optional - bundle remains valid without them

## Version Support Matrix

| CLI Version | v1.0 Support | v1.1 Support |
|-------------|--------------|--------------|
| v0.1.0 - v0.21.0 | ✅ Full | ❌ Not available |
| v0.21.1+ | ✅ Full | ✅ Full |

## Best Practices

### For Bundle Authors

1. **Use latest schema version**: Set `schema_version: "1.1"` for new bundles
2. **Keep change tracking optional**: Don't require change tracking for core functionality
3. **Document schema version**: Include schema version in bundle documentation

### For Adapter Developers

1. **Support both versions**: Check schema version before loading change tracking
2. **Graceful degradation**: Return `None` if change tracking not available
3. **Cross-repository support**: Use `external_base_path` for cross-repo configurations

## Related Documentation

- [Architecture - Change Tracking Models](../reference/architecture.md#change-tracking-models-v11-schema) - Technical details
- [Architecture - Bridge Adapter Interface](../reference/architecture.md#bridge-adapter-interface) - Adapter implementation guide
- [Directory Structure](directory-structure.md) - Bundle file organization
