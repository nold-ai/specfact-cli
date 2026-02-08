# Change: Bridge Registry for Cross-Module Service Interoperability

## Why


`arch-04-core-contracts-interfaces` formalizes module IO contracts and core isolation, but modules still lack a standard way to expose reusable external-service schema converters. Without a bridge registry, modules either duplicate adapter logic or reintroduce coupling, which slows parallel development and blocks marketplace-ready interoperability.

## What Changes


- **NEW**: Add `src/specfact_cli/registry/bridge_registry.py` with `SchemaConverter` protocol and `BridgeRegistry` for converter registration/discovery.
- **MODIFY**: Extend module package metadata to declare `service_bridges` in `module-package.yaml`.
- **MODIFY**: Extend module lifecycle registration to validate and register declared service bridges without direct core-to-module imports.
- **MODIFY**: Add backlog bridge converter implementations (ADO, Jira, Linear, GitHub) under module-local adapters and register them via manifest metadata.
- **NEW**: Add user and developer documentation for bridge registry usage and custom bridge mappings.
- **NEW**: Add tests for bridge registry behavior, manifest parsing, registration-time validation, and module integration.

## Capabilities
### New Capabilities

- `bridge-registry`: Contract-driven registry for service schema converters so modules can publish and consume conversion bridges without hardcoded core logic.

### Modified Capabilities

- `module-packages`: Extend module package manifest schema with declarative bridge metadata.
- `module-lifecycle-management`: Extend discovery/registration flow to validate and register bridge converters safely.
- `backlog-adapter`: Add bridge converter implementations and mapping behaviors for backlog service integrations.

## Impact

- **Affected specs**: New spec for `bridge-registry`; delta specs for `module-packages`, `module-lifecycle-management`, and `backlog-adapter`.
- **Affected code**:
  - `src/specfact_cli/registry/bridge_registry.py` (new)
  - `src/specfact_cli/registry/module_packages.py` (bridge metadata loading and registration)
  - `src/specfact_cli/models/module_package.py` (service bridge metadata)
  - `src/specfact_cli/modules/backlog/src/adapters/*.py` (new converter modules)
  - `tests/unit/registry/test_bridge_registry.py` (new)
  - `tests/unit/registry/test_module_bridge_registration.py` (new)
- **Affected documentation**:
  - `docs/reference/bridge-registry.md` (new)
  - `docs/guides/creating-custom-bridges.md` (new)
  - `docs/reference/architecture.md` and `docs/_layouts/default.html` (updated navigation and architecture notes)
- **Integration points**: module discovery, manifest parsing, registry startup, backlog adapters, sync workflows.
- **Backward compatibility**: Backward compatible. Modules without `service_bridges` remain valid and continue working.
- **Rollback plan**: Disable bridge registration in module lifecycle and remove `service_bridges` manifest handling; modules continue with existing adapter behavior.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #207
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/207>
- **Last Synced Status**: proposed
- **Sanitized**: false
