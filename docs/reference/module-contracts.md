---
layout: default
title: Module Contracts
permalink: /reference/module-contracts/
description: ModuleIOContract protocol, validation output model, and isolation rules for module developers.
---

# Module Contracts

SpecFact modules integrate through a protocol-first interface and inversion-of-control loading.

## ModuleIOContract

`ModuleIOContract` defines four operations:

- `import_to_bundle(source: Path, config: dict) -> ProjectBundle`
- `export_from_bundle(bundle: ProjectBundle, target: Path, config: dict) -> None`
- `sync_with_bundle(bundle: ProjectBundle, external_source: str, config: dict) -> ProjectBundle`
- `validate_bundle(bundle: ProjectBundle, rules: dict) -> ValidationReport`

Implementations should use runtime contracts (`@icontract`) and runtime type validation (`@beartype`).

## ValidationReport

`ValidationReport` provides structured validation output:

- `status`: `passed | failed | warnings`
- `violations`: list of maps with `severity`, `message`, `location`
- `summary`: counts (`total_checks`, `passed`, `failed`, `warnings`)

## Inversion of Control

Core code must not import module code directly.

- Allowed: core -> `CommandRegistry`
- Forbidden: core -> `specfact_cli.modules.*`

Module discovery and loading are done through registry-driven lazy loading.

## Migration and Compatibility

During the migration from hard-wired command paths:

- New feature logic belongs in `src/specfact_cli/modules/<module>/src/commands.py`.
- Legacy files under `src/specfact_cli/commands/*.py` are shims for backward compatibility.
- Only `app` re-export behavior is guaranteed from shim modules.
- New code should import from module-local command paths, not shim paths.

This enables module-level evolution while keeping core interfaces stable.

## Example Implementation

```python
@beartype
@require(lambda source: source.exists())
@ensure(lambda result: isinstance(result, ProjectBundle))
def import_to_bundle(source: Path, config: dict[str, Any]) -> ProjectBundle:
    return ProjectBundle.load_from_directory(source)
```

## Guidance for 3rd-Party Modules

- Declare module metadata in `module-package.yaml`.
- Implement as many protocol operations as your module supports.
- Declare `schema_version` when you depend on a specific bundle IO schema.
- Keep module logic isolated from core; rely on registry entrypoints.
