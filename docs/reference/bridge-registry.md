---
layout: default
title: Bridge Registry
permalink: /reference/bridge-registry/
---

# Bridge Registry

The bridge registry enables module-declared converters to translate external service payloads into
ProjectBundle-compatible structures without direct core imports from module internals.

## Core Concepts

- `SchemaConverter`: protocol with `to_bundle(external_data: dict) -> dict` and
  `from_bundle(bundle_data: dict) -> dict`.
- `BridgeRegistry`: runtime registry keyed by `bridge_id` and owned by module name.
- `service_bridges`: module manifest metadata used by lifecycle registration.

## Manifest Declaration

Module manifests can declare bridges:

```yaml
service_bridges:
  - id: ado
    converter_class: specfact_cli.modules.backlog.src.adapters.ado.AdoConverter
    description: Azure DevOps backlog payload converter
```

Required keys:

- `id`
- `converter_class` (fully-qualified dotted class path)

## Lifecycle Behavior

- Enabled/compatible modules are processed by `register_module_package_commands()`.
- Valid bridge declarations are imported and registered in the shared `BridgeRegistry`.
- Invalid declarations are skipped with warnings and do not block startup.
- Duplicate bridge IDs are handled deterministically (first registration kept, later duplicates skipped).

## Protocol Reporting

Lifecycle protocol reporting now uses the effective runtime interface:

- `runtime_interface` if exposed
- `commands` if exposed
- otherwise module entrypoint object

The summary format is:

`Protocol-compliant: <compliant>/<total> modules (Full=<n>, Partial=<n>, Legacy=<n>)`

