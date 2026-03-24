---
layout: default
title: Module Development Guide
permalink: /guides/module-development/
description: How to build and package SpecFact CLI modules.
---

# Module Development Guide

This guide defines the required structure and contracts for authoring SpecFact modules.

> Modules docs handoff: this page remains in the core docs set as release-line overview content.
> Canonical bundle-specific deep guidance now lives in the canonical modules docs site, currently
> published at `https://modules.specfact.io/`.

Official workflow bundle implementation now lives in the dedicated `nold-ai/specfact-cli-modules`
repository. `specfact-cli` owns the lean runtime, registry, marketplace lifecycle, shared
contracts, and bundle loading/orchestration surfaces consumed by installed bundles.

## Required structure

```text
specfact-cli-modules/
  packages/<bundle-package>/
    pyproject.toml
    src/<bundle_namespace>/<command_or_feature>/
      __init__.py
      app.py
      commands.py

specfact-cli/
  src/specfact_cli/
    registry/
    groups/
    common/
    adapters/
    models/
```

For local/project-scoped modules discovered by the CLI, keep the configured module root structure
under `<repo>/.specfact/modules` or `~/.specfact/modules` and ensure marketplace metadata remains
compatible with the runtime loader.

## `module-package.yaml` schema

Required fields:

- `name`: module or bundle identifier
- `version`: semantic version string
- `commands`: command names provided by this module or package entrypoint

Common optional fields:

- `command_help`
- `pip_dependencies`
- `module_dependencies`
- `core_compatibility`
- `tier`
- `addon_id`

Extension/security fields:

- `schema_extensions`
- `service_bridges`
- `publisher`
- `integrity`

## Command code expectations

- `src/app.py` exposes the Typer `app` used by registry loaders.
- `src/commands.py` holds command handlers and options.
- Public APIs should use contract-first decorators:
  - `@icontract` (`@require`, `@ensure`)
  - `@beartype`

## Naming and design conventions

- File/module names: `snake_case`
- Classes: `PascalCase`
- Keep command implementations scoped to module boundaries.
- Use `get_bridge_logger` for production command logging paths.

## Integration checklist

1. Add or update the package/module manifest (`module-package.yaml`) and package metadata in the modules repository.
2. Implement command entrypoints in the bundle package namespace.
3. Ensure runtime loader/import paths remain compatible with `specfact-cli` registry discovery and bundle grouping.
4. Run format/type-check/lint/contract/signature checks in the owning repository.
5. Keep core-only docs and runtime contracts in `specfact-cli`; keep bundle behavior/docs with the modules repo whenever possible.

## Related docs

- [Architecture Reference](../architecture/overview.md)
- [Module System Architecture](../architecture/module-system.md)
- [Adapter Development Guide](adapter-development.md)
