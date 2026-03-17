---
layout: default
title: Module Contracts
permalink: /reference/module-contracts/
description: ModuleIOContract protocol, validation output model, and isolation rules for module developers.
---

# Module Contracts

SpecFact modules integrate through a protocol-first interface and inversion-of-control loading.

> Modules docs handoff: this page remains in the core docs set because it documents runtime-facing
> contracts and core isolation rules. Bundle-specific contract implementation guidance lives in the
> canonical modules docs site, currently published at
> `https://modules.specfact.io/`.

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

Core runtime must not import external bundle package namespaces directly.

- Allowed:
  - core runtime -> `CommandRegistry`
  - bundle packages -> `specfact_cli` shared contracts, adapters, models, utils
- Forbidden:
  - core runtime -> `specfact_backlog.*`, `specfact_project.*`, `specfact_codebase.*`, or other external bundle package namespaces
  - bundle packages reaching back into unpublished/private core internals outside supported contracts

Module discovery and loading are done through registry-driven lazy loading.

## Migration and Compatibility

During the migration from hard-wired command paths:

- Official workflow bundle logic now belongs in `nold-ai/specfact-cli-modules`.
- Legacy files under `src/specfact_cli/commands/*.py` are shims for backward compatibility.
- Only `app` re-export behavior is guaranteed from shim modules.
- Lean-core runtime code in `specfact-cli` should depend on shared contracts and loader interfaces, not on bundle implementation modules.
- Bundle packages should import stable runtime surfaces from `specfact_cli` and expose their own entrypoints from package-local namespaces.

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
- Follow the same ownership split used by `specfact-cli-modules`: bundle behavior lives outside
  the core runtime repository whenever possible.
