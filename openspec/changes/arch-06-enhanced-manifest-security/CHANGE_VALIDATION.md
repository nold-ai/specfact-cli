# Change Validation Report: arch-06-enhanced-manifest-security

**Validation Date**: 2026-02-08
**Change Proposal**: [proposal.md](./proposal.md)
**Validation Method**: Dry-run dependency analysis and strict OpenSpec validation

## Executive Summary

- **Breaking Changes**: 0 detected (proposal is additive and policy-gated)
- **Primary Impact Areas**: module manifest parsing, module registration lifecycle, module install flow
- **Risk Level**: Medium (security controls affect module enable/install behavior)
- **Validation Result**: Pass

## Interface/Contract Impact

## New/extended interfaces

- `ModulePackageMetadata` extensions for publisher/integrity/versioned dependencies
- New `crypto_validator` helper interface for checksum/signature checks
- Registration/install policy gate for unsigned modules

## Compatibility assessment

- Existing manifests remain compatible if new metadata fields are optional.
- Unsigned module behavior remains backward compatible when strict trust mode is not forced.
- No required signature changes to existing CLI command interfaces were introduced in proposal artifacts.

## Dependent Code Analysis

Search-based dependency scan identified direct coupling points that must be considered during implementation:

- `src/specfact_cli/registry/module_packages.py`
  - Current source of truth for `ModulePackageMetadata`
  - Parsing logic for `module-package.yaml` and lifecycle validation
- `src/specfact_cli/registry/bootstrap.py`
  - Calls `register_module_package_commands()`; trust checks must not break startup resilience
- `src/specfact_cli/modules/init/src/commands.py`
  - Reads discovered packages; UX/messages may need updates for trust failures
- `src/specfact_cli/registry/module_state.py`
  - Consumes dependency metadata; versioned dependency structures may affect expectations
- `tests/unit/specfact_cli/registry/test_module_packages.py`
- `tests/unit/specfact_cli/registry/test_module_dependencies.py`
- `tests/unit/specfact_cli/registry/test_version_constraints.py`
- `tests/unit/specfact_cli/registry/test_init_module_lifecycle_ux.py`

## Notable implementation caveat

The proposal references `src/specfact_cli/models/module_package.py`, but the current active metadata model is defined in `src/specfact_cli/registry/module_packages.py`. Implementation should either:

1. Keep changes in `src/specfact_cli/registry/module_packages.py`, or
2. Introduce a new model module and refactor imports safely.

This is a scope/placement consideration, not a breaking-change blocker.

## Breaking Change Analysis

No immediate breaking changes are required by this proposal if implemented as follows:

- New manifest fields are optional with safe defaults.
- Trust enforcement defaults to checksum baseline + explicit strict policy for signature/unsigned handling.
- Failed trust checks remain module-local (skip/reject offending module) without crashing unrelated module registration.

## OpenSpec Validation

- Command: `openspec validate arch-06-enhanced-manifest-security --strict`
- Result: `Change 'arch-06-enhanced-manifest-security' is valid`

## Recommendation

Proceed to implementation with explicit test coverage for:

- Legacy manifest parsing compatibility
- Trust failure isolation (one module fails, others continue)
- Unsigned-module policy behavior in strict and non-strict modes
