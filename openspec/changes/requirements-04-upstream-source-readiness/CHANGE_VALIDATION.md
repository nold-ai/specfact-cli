# Change Validation Report: requirements-04-upstream-source-readiness

**Validation Date**: 2026-07-17 Europe/Berlin
**Change Proposal**: [proposal.md](./proposal.md)
**Validation Method**: Interface dry run in `/private/tmp/specfact-validation-requirements-04`, dependency search, strict OpenSpec validation, focused tests, and repository quality-gate verification.

## Executive Summary

- Breaking Changes: 0 detected
- Dependent Files: 3 affected
- Impact Level: Medium
- Validation Result: Pass
- User Decision: Resolved the readiness policy as `validation.openspec.require_native_validation`; the enterprise tier defaults it to `true`, and the compatibility fixture is pinned to Spec Kit `v0.12.18`.

## Breaking Changes Detected

None. `import_openspec_change` adds optional keyword-only `profile` and
`project_root` parameters, preserving its existing one-argument call contract.

## Dependencies Affected

### Critical Updates Required

- `src/specfact_cli/requirements/importers.py`: add atomic readiness gates before normalization.
- `src/specfact_cli/requirements/context.py`: resolve the layered native-validation policy.

### Recommended Updates

- `tests/unit/requirements/test_upstream_evidence_imports.py`: fixture-backed source-readiness and policy tests.
- `docs/reference/requirements-context-adapter.md`: document diagnostics and layered policy behavior.

## Impact Assessment

- **Code Impact**: Read-only source import behavior becomes fail-closed for incomplete inputs; accepted source IDs, revisions, and scenarios remain unchanged.
- **Test Impact**: Native importer and profile-resolution regression coverage.
- **Quality-Gate Impact**: The workflow uses the configured line-coverage threshold and propagates quality-gate failures through its log pipeline.
- **Documentation Impact**: Requirements adapter reference documents readiness diagnostics and policy configuration.
- **Release Impact**: Minor feature; version/release work remains a delivery task after this PR is accepted.

## Format Validation

- **proposal.md Format**: Pass under repository strict OpenSpec validation.
- **tasks.md Format**: Pass; tests precede production edits and evidence is recorded in `TDD_EVIDENCE.md`.
- **specs Format**: Pass; scenarios cover incomplete sources, required validator failure, unavailable validators, and portable imports.
- **Config.yaml Compliance**: Pass.

## OpenSpec Validation

- **Status**: Pass
- **Command**: `openspec validate requirements-04-upstream-source-readiness --strict --json`
- **Issues Found/Fixed**: 0

## Validation Artifacts

- Temporary interface workspace: `/private/tmp/specfact-validation-requirements-04`
- Failing-before and passing-after commands: [TDD_EVIDENCE.md](./TDD_EVIDENCE.md)
- The sibling internal repository is available, but it has no
  `wiki/sources/requirements-04-upstream-source-readiness.md` mirror to update;
  create that tracking page before release coordination if it becomes required.
