---
layout: default
title: Module Development Guide
permalink: /guides/module-development/
description: How to build and package SpecFact CLI modules.
---

# Module Development Guide

This guide defines the required structure and contracts for authoring SpecFact modules.

## Required structure

```text
src/specfact_cli/modules/<module-name>/
  module-package.yaml
  src/
    __init__.py
    app.py
    commands.py
```

For workspace-level modules, keep the same structure under the configured modules root.

## `module-package.yaml` schema

Required fields:

- `name`: module identifier
- `version`: semantic version string
- `commands`: top-level command names provided by this module

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

1. Add `module-package.yaml`.
2. Implement `src/app.py` and `src/commands.py`.
3. Ensure loader/import path works with registry discovery.
4. Run format/type-check/lint/contract checks.

## Related docs

- [Architecture Reference](../reference/architecture.md)
- [Module System Architecture](../architecture/module-system.md)
- [Adapter Development Guide](adapter-development.md)
