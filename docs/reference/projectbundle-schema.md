---
layout: default
title: ProjectBundle Schema
permalink: /reference/projectbundle-schema/
description: ProjectBundle fields, schema_version semantics, and compatibility guidance.
---

# ProjectBundle Schema

`ProjectBundle` is the canonical IO contract used by core and module integrations.

## Key Fields

- `manifest`: bundle metadata and indexes (`BundleManifest`)
- `bundle_name`: logical bundle identifier
- `schema_version`: module-IO schema version string (default: `"1"`)
- `idea`, `business`, `product`, `features`, `clarifications`: project content

## Schema Versioning Strategy

`schema_version` is a compatibility signal for module IO behavior.

- Major compatibility checks in module registration compare module-declared schema version with current ProjectBundle schema.
- Missing module schema version is treated as compatible with the current schema.
- Incompatible module schema versions are skipped at registration time.

## Example

```yaml
bundle_name: legacy-api
schema_version: "1"
manifest:
  versions:
    schema: "1.0"
    project: "0.1.0"
product:
  themes: []
  releases: []
features: {}
```

## Backward Compatibility

- Existing bundles without explicit module metadata remain usable.
- Registration keeps legacy modules enabled when protocol methods are absent.
- New protocol and schema checks are additive and designed for gradual migration.
