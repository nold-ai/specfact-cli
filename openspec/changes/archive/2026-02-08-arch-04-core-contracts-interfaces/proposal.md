# Change: Core Contracts and Module Interface Formalization

## Why

The modular architecture (arch-01/02/03) provides strong encapsulation for parallel module development, but the core IO contract is not formally defined or enforced. Modules can still directly import from each other and core lacks explicit protocol definitions for module behavior. To enable a true marketplace for 3rd-party and community modules, we must formalize ProjectBundle as the ONLY IO contract and enforce zero core→module dependencies through static analysis. This establishes the contract foundation that all subsequent marketplace phases build upon.

## What Changes

- **NEW**: Create `src/specfact_cli/contracts/module_interface.py` with `ModuleIOContract` protocol defining the four core operations all modules must implement: `import_to_bundle()`, `export_from_bundle()`, `sync_with_bundle()`, and `validate_bundle()`
- **NEW**: Add static analysis enforcement via `tests/unit/test_core_module_isolation.py` that parses AST and fails if core CLI code imports from `specfact_cli.modules.*`
- **MODIFY**: Update existing modules (backlog, sync, plan, generate, enforce) to implement `ModuleIOContract` interface
- **NEW**: Document ProjectBundle schema versioning in `docs/reference/projectbundle-schema.md`
- **NEW**: Document module contract requirements in `docs/reference/module-contracts.md`
- **NEW**: Add CI enforcement of core isolation via static analysis test

## Capabilities

### New Capabilities

- `module-io-contract`: Protocol definition for module interfaces with ProjectBundle as the sole IO contract (import, export, sync, validate operations)
- `core-module-isolation`: Static analysis enforcement preventing core CLI from importing module code, maintaining zero-dependency inversion-of-control architecture

### Modified Capabilities

- `module-packages`: Extend module package metadata and discovery to validate ModuleIOContract implementation
- `module-lifecycle-management`: Extend registration-time validation to check ModuleIOContract conformance

## Impact

- **Affected specs**: New specs for `module-io-contract` and `core-module-isolation`; delta specs for `module-packages` and `module-lifecycle-management`
- **Affected code**:
  - `src/specfact_cli/contracts/` (new directory and module_interface.py)
  - `src/specfact_cli/modules/*/src/commands.py` (backlog, sync, plan, generate, enforce)
  - `src/specfact_cli/registry/module_packages.py` (contract validation)
  - `tests/unit/test_core_module_isolation.py` (new)
  - `.github/workflows/tests.yml` (add isolation test)
- **Affected documentation**: New reference docs for ProjectBundle schema and module contracts; update architecture docs with contract-first module development patterns
- **Integration points**: Module discovery, registration-time validation, future marketplace module verification
- **Backward compatibility**: Non-breaking; adds formalized contracts to existing patterns. Existing modules work as-is but will be updated to explicitly implement the protocol.
- **Release version**: Minor version bump (new feature/refactor, backward compatible)

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #206
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/206>
- **Last Synced Status**: in-progress
- **Sanitized**: false
