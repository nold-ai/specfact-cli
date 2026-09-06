# Change Validation Report: fix-retained-red-proof-provenance

**Validation Date**: 2026-08-26 (Europe/Berlin)
**Change Proposal**: [proposal.md](./proposal.md)
**Validation Method**: Static producer/validator/workflow boundary analysis against `origin/dev`

## Executive Summary

- Breaking Changes: 0 detected
- Impact Level: Low and release-blocking
- Validation Result: Pass

## Dependency and interface analysis

- No package dependency, public CLI/API, evidence schema reader, or module fixture changes are required.
- Complete retained reports keep their current shape and validation semantics.
- The change fills fields the validator already requires; it does not add a compatibility reader for incomplete reports.
- Requirements 08's signed replay-capsule boundary is independent and unchanged.

## Affected files and required updates

- The primary Requirements delivery changes are in
  `.github/workflows/requirements-evidence.yml`,
  `scripts/requirements_proof_pytest_plugin.py`,
  `scripts/requirements_proof_provenance.py`, and
  `scripts/requirements_bootstrap_authority.py`.
- Reproducible-delivery audit wiring is updated in
  `scripts/check_reproducible_delivery.py` and
  `scripts/refresh_reproducible_delivery.py`. The isolated review-tool closure
  is recorded in
  `requirements/code-review/requirements.in` and
  `requirements/code-review/locked.txt`; it does not enter the runtime package.
- Focused regressions, including proof-executor coverage, live under
  `tests/unit/scripts/` and `tests/unit/workflows/`. No downstream consumer
  migration is required because the existing validator contract is preserved.
- The required update is producer-side completion of retained RED provenance.
  The recommended operational control is to retain the immutable workflow
  artifact and exact-head Requirements result with the release evidence.

## Validation evidence

- **Failing-before** (`2026-08-26 22:34` Europe/Berlin): the four focused
  provenance/plugin/executor/workflow selectors exited 1 with four intended
  failures before production edits.
- **Passing-after focused control** (`2026-08-27 00:42` Europe/Berlin):
  `SPECFACT_MODULES_REPO=<PINNED_MODULE_FIXTURE> UV_CACHE_DIR=<UV_CACHE> hatch run test tests/unit/scripts/test_requirements_bootstrap_authority.py tests/unit/scripts/test_requirements_proof_provenance_security.py`
  passed all 14 tests.
- **Full regression** (`2026-08-27 00:44` Europe/Berlin):
  `SPECFACT_MODULES_REPO=<PINNED_MODULE_FIXTURE> UV_CACHE_DIR=<UV_CACHE> hatch run test`
  recorded 3,033 passed and 9 skipped. Two sandbox-only environment controls
  were recorded explicitly in `TDD_EVIDENCE.md`; the network control passed on
  rerun and the GitHub Tests job supplied the writable-home terminal control.
- **Final Requirements gate**: run `33106636809` succeeded at exact head
  `595a74e2d000b0c19a71a4af9d178d87480dfb63`; retained artifact
  `requirements-evidence` has ID `9660752140`.
- **Strict specification validation**:
  `openspec validate fix-retained-red-proof-provenance --strict` passed.

## Documentation and release analysis

- Contributor-facing OpenSpec/TDD evidence is affected.
- README, user guides, docs index, and navigation do not describe this internal CI producer and require no change.
- Issue #686 owns the single `0.55.2` version/changelog/release transaction; this prerequisite must merge before that release rather than consuming `0.55.2` independently.
- Release remains blocked if the final Requirements artifact, exact-head
  association, or strict OpenSpec validation cannot be reproduced. No gate was
  unavailable in the final GitHub run.

## Rollback

Revert the prerequisite PR before release. If a regression ships in `0.55.2`, publish a forward patch and retain normal tag/PyPI history.

## OpenSpec validation

- **Command**: `openspec validate fix-retained-red-proof-provenance --strict`
- **Result**: pass; no format or scenario issues.
