# Design: Module Lifecycle Management

## Context

`arch-02` moved commands into module packages and introduced manifest metadata, but the runtime registry still treats dependency metadata as advisory. This change adds enforcement for dependency and compatibility constraints without introducing startup fragility.

## Goals

- Enforce module dependency integrity during command registration.
- Enforce module-to-core compatibility through PEP 440 specifier evaluation.
- Prevent unsafe module disabling unless operator explicitly overrides.
- Remove cross-module private helper imports by moving shared utility logic to core `utils`.
- Preserve command startup resilience by skipping invalid modules with debug logging instead of hard-failing startup.

## Non-Goals

- Versioned inter-module dependency constraints (for example `sync>=0.29.0`).
- Runtime hot-reload of module enable/disable state.
- Plugin marketplace or remote module resolution.

## Architecture

### 1. Shared Helper Extraction

Move reusable conversion and constitution helper functions into `src/specfact_cli/utils/bundle_converters.py` and redirect cross-module imports to this core utility. Keep compatibility wrappers in original module command files where needed.

### 2. Manifest Schema Extension

Add optional `core_compatibility` to `ModulePackageMetadata` and to all `module-package.yaml` manifests. Parsing remains tolerant: absent field means compatible with all core versions.

### 3. Registration-Time Lifecycle Validation

During `register_module_package_commands()`:

1. Evaluate module enablement state.
2. Validate `core_compatibility` against CLI version.
3. Validate declared `module_dependencies` are discovered and enabled.
4. Register only valid modules; skip invalid modules with debug-level reason.

This preserves startup continuity while enforcing lifecycle guarantees.

### 4. Safe Disable Enforcement

Before persisting disable operations in `init`:

1. Compute effective enabled state.
2. Compute reverse dependencies for requested disables.
3. Block operation when enabled dependents exist.
4. Allow override with `--force` and explicit warning behavior.

## Contracts and Testing Strategy

- Add `@beartype` and `@icontract` usage for newly introduced public helper/validation APIs.
- Add focused tests for:
  - dependency validation outcomes,
  - compatibility specifier outcomes,
  - safe-disable reverse dependency detection,
  - extracted bundle conversion helpers,
  - boundary guard against cross-module `src.commands` imports.
- Maintain contract-first validation gates and spec-to-test traceability.

## Rollout

- Implement in phases from helper extraction to registry checks to safe-disable and boundary tests.
- Verify with format, type-check, contract-test, and scenario-relevant test runs.
- Include documentation/version/changelog updates before PR.

## Risks and Mitigations

- **Risk**: Invalid compatibility specifier strings could block modules unexpectedly.
  - **Mitigation**: Treat parse failures as non-blocking compatibility and log debug diagnostics.
- **Risk**: Users may be surprised when disabling modules is blocked.
  - **Mitigation**: Provide explicit error with dependent module list and `--force` hint.
- **Risk**: Boundary guard may flag legitimate imports.
  - **Mitigation**: Scope rule to non-`app` imports from other modules' `src.commands` only.
