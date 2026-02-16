---
layout: default
title: Using Module Security and Schema Extensions
permalink: /guides/using-module-security-and-extensions/
description: How to use arch-06 (module security) and arch-07 (schema extensions) from CLI commands and as a module author.
nav_order: 22
---

# Using Module Security and Schema Extensions

With **arch-06** (manifest security) and **arch-07** (schema extension system) in place, you can use verified modules and store module-specific metadata on bundles and features. This guide shows how to utilize these features from the CLI and in your own modules.

## Quick reference

| Capability | What it does | Where to read more |
|------------|--------------|--------------------|
| **arch-06** | Publisher + integrity (checksum/signature) on module manifests; versioned dependencies | [Module Security](/reference/module-security/) |
| **arch-07** | `extensions` dict on Feature/ProjectBundle; `get_extension`/`set_extension`; `schema_extensions` in manifest | [Extending ProjectBundle](/guides/extending-projectbundle/) |

---

## Using arch-06 (module security)

### As a CLI user (consuming modules)

- **Verified modules**: When you run any command that loads modules (e.g. `specfact backlog ...`, `specfact project ...`), the registry discovers modules and, when a module has `integrity.checksum` in its `module-package.yaml`, verifies the manifest checksum before registering. If verification fails, that module is skipped and a warning is logged; other modules still load.
- **Unsigned modules**: Modules without `integrity` metadata are allowed by default (backward compatible). To document explicit opt-in in strict environments, set:
  ```bash
  export SPECFACT_ALLOW_UNSIGNED=1
  ```
- **Versioned dependencies**: Manifests can declare `module_dependencies_versioned` and `pip_dependencies_versioned` (each entry: `name`, `version_specifier`) for install-time resolution. You don’t need to do anything special; the installer uses these when present.

You don’t run a separate “verify” command; verification happens automatically at module registration when the CLI starts.

### As a module author (publishing a module)

1. **Add publisher and integrity to `module-package.yaml`** (optional but recommended):

   ```yaml
   name: my-module
   version: "0.1.0"
   commands: [my-group]

   publisher:
     name: "Your Name or Org"
     email: "contact@example.com"

   integrity:
     checksum: "sha256:<hex>"   # Required for verification
     signature: "<base64>"      # Optional; requires trusted key on consumer side
   ```

2. **Generate the checksum** using the bundled script:

   ```bash
   ./scripts/sign-module.sh path/to/module-package.yaml
   # Output: sha256:<hex>
   # Add that value to integrity.checksum in the manifest
   ```

3. **CI**: Use `.github/workflows/sign-modules.yml` (or equivalent) to produce or validate checksums when manifest files change.

4. **Versioned dependencies** (optional):

   ```yaml
   module_dependencies_versioned:
     - name: backlog-core
       version_specifier: ">=0.2.0"
   pip_dependencies_versioned:
     - name: requests
       version_specifier: ">=2.28.0"
   ```

Details: [Module Security](/reference/module-security/).

---

## Using arch-07 (schema extensions)

### As a CLI user (running commands that use extensions)

Several commands already read or write extension data on `ProjectBundle` (and its manifest). You use them as usual; extensions are persisted with the bundle.

- **Link a backlog provider** (writes `backlog_core.backlog_config` on project metadata):
  ```bash
  specfact project link-backlog --bundle my-bundle --adapter github --project-id my-org/my-repo
  ```
- **Health check and other project commands** read that same extension to resolve adapter/project/template:
  ```bash
  specfact project health-check --bundle my-bundle
  ```

Any command that loads a bundle (e.g. `specfact plan ...`, `specfact sync ...`, `specfact spec ...`) loads the full bundle including `extensions`; round-trip save keeps extension data. So you don’t need a special “extensions” command to benefit from them—they’re part of the bundle.

**Introspecting registered extensions (programmatic):** There is no `specfact extensions list` CLI yet. From Python you can call:

```python
from specfact_cli.registry.extension_registry import get_extension_registry
all_exts = get_extension_registry().list_all()  # dict: module_name -> list of SchemaExtension
```

### As a module author (using extensions in your commands)

1. **Declare extensions** in `module-package.yaml` so the CLI can validate and avoid collisions:

   ```yaml
   schema_extensions:
     - target: Feature
       field: my_custom_id
       type_hint: str
       description: My module’s external ID for this feature
     - target: ProjectBundle
       field: last_sync_ts
       type_hint: str
       description: ISO timestamp of last sync
   ```

2. **In your command code**, when you have a `ProjectBundle` or `Feature` (e.g. from `load_bundle_with_progress` or from a plan bundle):

   ```python
   from specfact_cli.models.plan import Feature
   from specfact_cli.models.project import ProjectBundle

   # On a Feature
   feature.set_extension("my_module", "my_custom_id", "EXT-123")
   value = feature.get_extension("my_module", "my_custom_id")  # "EXT-123"
   missing = feature.get_extension("my_module", "other", default="n/a")  # "n/a"

   # On ProjectBundle (e.g. bundle.manifest.project_metadata or bundle itself)
   bundle.set_extension("my_module", "last_sync_ts", "2026-02-16T12:00:00Z")
   ts = bundle.get_extension("my_module", "last_sync_ts")
   ```

3. **Naming rules**: `module_name`: lowercase, alphanumeric + underscores/hyphens, **no dots**. `field`: lowercase, alphanumeric + underscores. Keys are stored as `module_name.field` (e.g. `my_module.my_custom_id`).

4. **Project metadata**: The built-in `project link-backlog` command uses **project_metadata** (on the bundle manifest), which also supports `get_extension`/`set_extension` with the same `module_name.field` convention (e.g. `backlog_core.backlog_config`). Use the same pattern for your module’s config stored on the project.

Full API and examples: [Extending ProjectBundle](/guides/extending-projectbundle/).

---

## Summary

- **arch-06**: Use `scripts/sign-module.sh` and `integrity`/`publisher` in manifests; consumers get automatic checksum verification at registration; set `SPECFACT_ALLOW_UNSIGNED=1` if you explicitly allow unsigned modules.
- **arch-07**: Use `get_extension`/`set_extension` on Feature and ProjectBundle in your module code; declare `schema_extensions` in `module-package.yaml`; use existing commands like `specfact project link-backlog` and `specfact project health-check` to see extensions in action.

For deeper reference: [Module Security](/reference/module-security/), [Extending ProjectBundle](/guides/extending-projectbundle/), [Architecture](/reference/architecture/).
