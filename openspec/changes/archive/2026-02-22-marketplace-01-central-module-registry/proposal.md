# Change: Central Module Registry MVP for Official Modules

## Why

The modular architecture (arch-01 through arch-07) provides strong encapsulation, but modules remain built-in to the CLI package with no discovery mechanism for external modules. To enable marketplace ecosystem growth, we need a central registry with module discovery, installation, and verification infrastructure supporting official NOLD AI modules as the MVP foundation.

## What Changes

- **NEW**: Create `nold-ai/specfact-cli-modules` GitHub repository with registry index and module publishing infrastructure
- **NEW**: Create `module-registry` module package exposing `specfact module` CLI commands for install/uninstall/search/list/upgrade operations
- **NEW**: Implement multi-location module discovery (built-in, marketplace, custom paths)
- **NEW**: Create marketplace client for fetching registry index and downloading module tarballs
- **NEW**: Create module installer with checksum verification and marketplace path management
- **MODIFY**: Extend module discovery to scan multiple locations (~/.specfact/marketplace-modules, ~/.specfact/custom-modules)
- **NEW**: Add registry index.json schema with module metadata (id, namespace, version, download URLs, checksums)
- **NEW**: Add documentation for installing modules and marketplace usage
- **MODIFY**: Harmonize module lifecycle UX by keeping `specfact init --enable-module/--disable-module/--list-modules` as deprecated compatibility aliases while centralizing lifecycle management under `specfact module`

## Capabilities

### New Capabilities

- `module-marketplace-registry`: Central module registry with index.json schema, module metadata, and download infrastructure
- `module-installation`: CLI commands and infrastructure for installing/uninstalling modules from marketplace or custom sources
- `multi-location-discovery`: Module discovery across built-in, marketplace, and custom installation paths

### Modified Capabilities

- `module-packages`: Extend discovery to support multi-location module scanning with source tracking (built-in vs marketplace vs custom)
- `module-lifecycle-management`: Extend registration to handle modules from multiple sources with namespace validation

## Impact

- **Affected code**:
  - `src/specfact_cli/modules/module_registry/` (new module package backing `specfact module` commands)
  - `src/specfact_cli/modules/init/src/commands.py` (deprecation-compatible delegation for lifecycle flags)
  - `src/specfact_cli/cli.py` (compatibility normalization behavior retained for bare interactive lifecycle flags)
  - `src/specfact_cli/registry/module_discovery.py` (new: multi-location discovery)
  - `src/specfact_cli/registry/marketplace_client.py` (new: registry client)
  - `src/specfact_cli/registry/module_installer.py` (new: installation logic)
  - `src/specfact_cli/registry/module_packages.py` (use multi-location discovery)
- **Affected specs**: New specs for `module-marketplace-registry`, `module-installation`, `multi-location-discovery`; delta specs for `module-packages` and `module-lifecycle-management`
- **Affected documentation**:
  - `docs/guides/installing-modules.md` (new)
  - `docs/guides/module-marketplace.md` (new)
  - `docs/reference/architecture.md` (marketplace architecture)
  - `docs/_layouts/default.html` (navigation update)
- **External dependencies**:
  - New repository: `nold-ai/specfact-cli-modules` (registry infrastructure)
  - Depends on arch-06 (Enhanced Manifest Security) for checksum verification
- **Integration points**: Module discovery, installation workflow, registry client, module verification
- **Backward compatibility**: Backward compatible via deprecation alias strategy (existing `init` lifecycle flags remain supported while `specfact module` is canonical)
- **Rollback plan**: Disable marketplace client, revert to built-in-only discovery

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #214
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/214>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
- **Sanitized**: false
