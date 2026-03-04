# Core Decoupling Inventory

## Classification: keep / move / interface

Analysis date: 2026-03-04

### Summary

- **Core import boundary**: Core (`src/specfact_cli/`) does NOT import from bundle packages (`backlog_core`, `bundle_mapper`). Boundary test enforces this.
- **Bundle dependencies on core**: Bundles import from `specfact_cli.adapters`, `specfact_cli.models`, `specfact_cli.utils`, `specfact_cli.registry`, `specfact_cli.contracts`, `specfact_cli.modules` — all shared infrastructure used by core commands and validators.

### Candidate components

| Component | Classification | Rationale |
|-----------|----------------|-----------|
| `specfact_cli.models.backlog_item` | **KEEP** | Used by core (versioning, validators) and bundles. Shared model. |
| `specfact_cli.models.plan` | **KEEP** | Used by core (validators, sync, utils) and bundles. Shared model. |
| `specfact_cli.models.project` | **KEEP** | Used by core (versioning, utils, bundle_loader) and bundles. Shared model. |
| `specfact_cli.models.dor_config` | **KEEP** | Used by backlog-core add command; core validators may use. Shared. |
| `specfact_cli.adapters.registry` | **KEEP** | Core infrastructure for adapter resolution. Bundles use for backlog adapters. |
| `specfact_cli.adapters.ado`, `github` | **KEEP** | Core adapters. Bundles use via registry and protocol. |
| `specfact_cli.utils.prompts` | **KEEP** | Used by core and backlog-core commands. Shared utility. |
| `specfact_cli.registry.bridge_registry` | **KEEP** | Protocol registry. Core and bundles use. |
| `specfact_cli.contracts.module_interface` | **KEEP (interface)** | Already an interface contract. Bundles implement. |
| `specfact_cli.modules.module_io_shim` | **KEEP (interface)** | Shim for bundle I/O. Core provides; bundles use. |

### Move candidates

**None identified.** All `specfact_cli` components used by bundles are also used by core (validators, sync, versioning, registry, init, module_registry, upgrade). No bundle-only components remain in core.

### Interface contracts (already in place)

- `ModuleIOContract` — bundles implement; core consumes via `module_io_shim`
- `AdapterRegistry` — core provides; bundles use for backlog adapters
- `BRIDGE_PROTOCOL_REGISTRY` — protocol registration; bundles register `BacklogGraphProtocol`

### Boundary enforcement

- **Test**: `test_core_does_not_import_from_bundle_packages` — fails if any file under `src/specfact_cli/` imports from `backlog_core` or `bundle_mapper`
- **Status**: Passes. No residual core→bundle coupling.
