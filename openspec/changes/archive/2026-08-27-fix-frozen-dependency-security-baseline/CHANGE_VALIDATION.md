# Change Validation Report: fix-frozen-dependency-security-baseline

**Validation Date**: 2026-08-26 (Europe/Berlin)
**Evidence Recorded**: 2026-08-26 22:18:31 CEST (signed evidence commit)
**Change Proposal**: [proposal.md](./proposal.md)
**Validation Method**: Configuration/interface dependency analysis with temporary workspace `<VALIDATION_WORKSPACE>`
**Environment Mapping**: `<VALIDATION_WORKSPACE>` was an ephemeral local directory; its host path is not part of the validation contract.

## Executive Summary

- Breaking Changes: 0 detected
- Dependent Files: 3 authoritative dependency inputs plus existing tests/release consumers
- Impact Level: Low
- Validation Result: Pass
- User Decision: N/A; no interface extension or breaking choice is required

## Breaking Changes Detected

None. The change modifies development/build-tool constraints and generated frozen
inputs only. It does not change public functions, classes, CLI parameters, schemas,
runtime dependencies, or module contracts.

## Dependencies Affected

### Critical Updates Required

- `pyproject.toml`: declare the patched pip floor on the two tooling surfaces and
  apply the authorized Hatchling/Setuptools constraints.
- `uv.lock`: resolve the complete graph from the declared inputs.
- `requirements/ci/locked.txt`: regenerate the hash-protected audit/install export
  from the same lock.

### Recommended Updates

- `tests/unit/scripts/test_reproducible_delivery.py`: enforce the durable patched
  tooling floor, Hatchling backend pin, and pip-free core invariant.
- `SECURITY.md`: align documented audit semantics with the current frozen/export,
  fail-on-every-unreviewed-advisory implementation.
- Canonical version sources and `CHANGELOG.md`: publish the required patch baseline.

## Impact Assessment

- **Code Impact**: no production Python code or public interface change.
- **Test Impact**: one focused configuration-policy assertion plus existing frozen
  delivery, package, Python-version, and release compatibility suites.
- **Documentation Impact**: security policy semantics and release changelog only;
  no README, docs landing page, guide, or navigation change is required.
- **Release Impact**: Patch (`0.55.1` to `0.55.2`).

## Format Validation

- **proposal.md Format**: Pass; Why, What Changes, Capabilities, Impact, rollback,
  dependencies, and source tracking are present.
- **tasks.md Format**: Pass; branch, spec, failing evidence, implementation, passing
  gates, docs/version, PR, archive/release, and cleanup are ordered.
- **specs Format**: Pass; the modified requirement is complete and new scenarios use
  Given/When/Then-compatible OpenSpec form.
- **Config.yaml Compliance**: Pass; public metadata, docs research, code review,
  quality gates, versioning, and worktree rules are represented.

## Dependency and Compatibility Analysis

- pip remains tooling-only through `pip-audit/pip-api` and `pip-tools`; core runtime
  remains unchanged.
- A no-write targeted solve found the existing 184-package graph compatible with a
  pip 26.2.1 target upgrade and no other resolved-package change. A second targeted
  solve changed only Twine 6.2.0 to 7.0.0 after the publication control exposed the
  metadata compatibility boundary.
- Hatchling 1.32.0 and Setuptools 84.x remain subject to existing no-isolation wheel,
  Python 3.11-3.13, pip/pipx/uv launcher, and release validation gates.
- Hatchling 1.32.0's Core Metadata 2.5 default is incompatible with frozen Twine
  6.2.0. Twine 7.0.0 explicitly restores validation/upload support for Core Metadata
  2.5, supports the repository's Python 3.11-3.13 range, and remains development-only.
  The only documented removal relevant to distribution metadata is rejection of
  never-standardized Core Metadata 2.0, which this project does not emit.
- The pre-existing `audit-01-reproducible-delivery` change owns the delivery
  architecture; this bugfix conforms to that current tree without editing its branch
  or planning artifacts.

## OpenSpec Validation

- **Status**: Pass
- **Command**: `openspec validate fix-frozen-dependency-security-baseline --strict`
- **Issues Found/Fixed**: 0

## Validation Artifacts

- Temporary workspace: `/private/tmp/specfact-validation-fix-frozen-dependency-security-baseline.kOyKA8`
- Failing audit and policy-test evidence: [TDD_EVIDENCE.md](./TDD_EVIDENCE.md)
