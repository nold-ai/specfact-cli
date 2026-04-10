# Change: Module Lifecycle Management for Dependencies, Compatibility, and Safe Disable

## Why

`arch-02` completed module package separation, but module lifecycle constraints are still unenforced at runtime. `module_dependencies` is currently declarative-only, module manifests do not constrain CLI core compatibility, and `init --disable-module` can disable required modules without preflight protection.

This creates avoidable runtime breakage and weakens contract-first guarantees for modular command loading. We need registry-time lifecycle validation and safe-disable protection while preserving backward compatibility.

## What Changes

- **NEW**: Add module lifecycle validation at registration time for dependency existence/enabled state and `core_compatibility` version constraints.
- **NEW**: Extend module manifests with `core_compatibility` (PEP 440 specifier string) across all module packages.
- **NEW**: Add safe-disable checks in `specfact init` so disabling a module fails when enabled dependents require it, with explicit `--force` override.
- **NEW**: Add `specfact init --list-modules` to show discovered installed modules with effective enabled/disabled status.
- **NEW**: Add interactive up/down module selection for enable/disable flows, with explicit-id enforcement in non-interactive mode.
- **NEW**: Split initialization behavior into bootstrap-first `specfact init` (no IDE template side effects) and `specfact init ide` for prompt/template setup.
- **NEW**: Extract shared bundle conversion and constitution helper utilities from cross-module command imports into `specfact_cli.utils.bundle_converters`.
- **NEW**: Add boundary guard coverage that blocks cross-module imports from `specfact_cli.modules.<other>.src.commands` for non-`app` symbols.
- **EXTEND**: Add contract-first tests for dependency validation, version compatibility behavior, extracted utility helpers, and safe-disable logic.
- **EXTEND**: Update user-facing documentation and changelog/version synchronization for lifecycle management behavior and module manifest schema.

## Capabilities

- **module-lifecycle-management**: Enforce module dependency integrity, version compatibility, safe-disable semantics, and module boundary hygiene.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #203
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/203>
- **Last Synced Status**: proposed
<!-- content_hash: d31176ea7ec82ec0 -->
