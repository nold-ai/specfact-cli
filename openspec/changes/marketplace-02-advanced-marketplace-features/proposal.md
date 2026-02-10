# Change: Advanced Marketplace Features for Production Readiness

## Why

marketplace-01 provides basic module installation from the central registry, but lacks dependency conflict resolution, namespace management, and custom registry support needed for production use. To enable enterprise adoption and third-party modules, we need dependency resolution, module aliasing, and multi-registry support.

## What Changes

- **NEW**: Implement pip-compile style dependency resolver for module pip_dependencies
- **NEW**: Add module alias system for namespace mapping (command shortcuts)
- **NEW**: Support custom registries with trust levels and priority ordering
- **NEW**: Add namespace collision detection and enforcement for marketplace modules
- **NEW**: Create module publishing pipeline with validation and automation
- **MODIFY**: Extend module commands with alias and add-registry subcommands
- **NEW**: Add documentation for publishing modules, custom registries, and dependency resolution

## Capabilities

### New Capabilities

- `dependency-resolution`: pip-compile style resolution of pip_dependencies across all installed modules with conflict detection
- `module-aliasing`: User-configurable aliases mapping command names to namespaced module IDs
- `custom-registries`: Support for multiple registry sources with trust levels and priority ordering
- `module-publishing`: Automated pipeline for validating, packaging, and publishing modules to registry

### Modified Capabilities

- `module-installation`: Extend installation to resolve and install pip dependencies with conflict detection
- `module-lifecycle-management`: Extend registration to enforce namespace requirements and detect collisions

## Impact

- **Affected code**:
  - `src/specfact_cli/registry/dependency_resolver.py` (new: pip-compile integration)
  - `src/specfact_cli/registry/alias_manager.py` (new: alias storage and resolution)
  - `src/specfact_cli/registry/custom_registries.py` (new: multi-registry management)
  - `src/specfact_cli/modules/module/src/commands.py` (add alias, add-registry commands)
  - `src/specfact_cli/registry/module_installer.py` (dependency resolution integration)
  - `scripts/publish-module.py` (new: publishing automation)
- **Affected specs**: New specs for `dependency-resolution`, `module-aliasing`, `custom-registries`, `module-publishing`; delta specs for `module-installation` and `module-lifecycle-management`
- **Affected documentation**:
  - `docs/guides/publishing-modules.md` (new)
  - `docs/guides/custom-registries.md` (new)
  - `docs/reference/dependency-resolution.md` (new)
  - `docs/_layouts/default.html` (navigation update)
- **External dependencies**:
  - pip-tools library for pip-compile functionality (optional, fallback to pip resolver)
- **Integration points**: Module installation, dependency resolution, registry management, command resolution
- **Backward compatibility**: Fully backward compatible (dependency resolution is additive, aliases are optional)
- **Rollback plan**: Disable dependency resolver, remove alias system, revert to single registry

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #215
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/215>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
- **Sanitized**: false
