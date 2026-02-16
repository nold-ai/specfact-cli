---
layout: default
title: Extending ProjectBundle
permalink: /guides/extending-projectbundle/
description: Add namespaced custom fields to Feature and ProjectBundle without modifying core models.
---

# Extending ProjectBundle

Modules can extend `Feature` and `ProjectBundle` with custom metadata using the **schema extension system** (arch-07). Extensions use namespace-prefixed keys so multiple modules can store data without conflicts.

## Overview

- **`extensions`** – A dict on `Feature` and `ProjectBundle` that stores module-specific data under keys like `backlog.ado_work_item_id` or `sync.last_sync_timestamp`.
- **`get_extension(module_name, field, default=None)`** – Read a value.
- **`set_extension(module_name, field, value)`** – Write a value.
- **`schema_extensions`** – Optional declaration in `module-package.yaml` so the CLI can validate and introspect which fields a module uses.

## Using Extensions in Code

```python
from specfact_cli.models.plan import Feature
from specfact_cli.models.project import ProjectBundle

# On a Feature (e.g. from a bundle)
feature.set_extension("backlog", "ado_work_item_id", "123456")
value = feature.get_extension("backlog", "ado_work_item_id")  # "123456"
missing = feature.get_extension("backlog", "missing", default="default")  # "default"

# On a ProjectBundle
bundle.set_extension("sync", "last_sync_timestamp", "2025-01-15T12:00:00Z")
ts = bundle.get_extension("sync", "last_sync_timestamp")
```

**Rules:**

- `module_name`: lowercase, alphanumeric plus underscores/hyphens, **no dots** (e.g. `backlog`, `sync`).
- `field`: lowercase, alphanumeric plus underscores (e.g. `ado_work_item_id`).
- Keys are stored as `module_name.field` (e.g. `backlog.ado_work_item_id`).

## Declaring Extensions in the Manifest

In `module-package.yaml` you can declare which extensions your module uses so the CLI can detect collisions and support introspection:

```yaml
name: backlog
version: "0.1.0"
commands: [backlog]

schema_extensions:
  - target: Feature
    field: ado_work_item_id
    type_hint: str
    description: Azure DevOps work item ID for sync
  - target: Feature
    field: jira_issue_key
    type_hint: str
    description: Jira issue key when using Jira adapter
  - target: ProjectBundle
    field: last_sync_timestamp
    type_hint: str
    description: ISO timestamp of last sync
```

- **target** – `Feature` or `ProjectBundle`.
- **field** – Snake_case field name (must match `[a-z][a-z0-9_]*`).
- **type_hint** – Documentation only (e.g. `str`, `int`).
- **description** – Human-readable description.

If two modules declare the same `(target, field)` (e.g. both declare `Feature.ado_work_item_id`), the second module’s schema extensions are skipped and an error is logged.

## Best Practices

- Use a single logical namespace per module (the module name).
- Prefer short, clear field names (`ado_work_item_id`, `last_sync_timestamp`).
- Document extensions in `schema_extensions` so other tools and docs can introspect them.
- Do not rely on extension values for core behavior; keep them as optional metadata.

## Backward Compatibility

- Existing bundles and features without an `extensions` field load with `extensions = {}`.
- Modules that omit `schema_extensions` load and run normally; no extensions are registered for them.
