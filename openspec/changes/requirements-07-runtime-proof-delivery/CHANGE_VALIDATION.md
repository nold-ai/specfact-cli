# Change Validation Report: requirements-07-runtime-proof-delivery

**Validation Date:** 2026-08-05 (Europe/Berlin)
**Change Proposal:** [proposal.md](./proposal.md)
**Validation Method:** dependency dry-run using a temporary workspace and the
immutable merged Modules #379 fixture.

## Executive Summary

- Breaking Changes: 0 detected
- Dependent Files: 6 direct core integration files
- Impact Level: Medium
- Validation Result: Pass
- User Decision: Pin only the published immutable fixture; do not use a
  mutable module branch.

## Dependency Analysis

Merged Modules PR #379 adds an optional `--legacy-tdd-evidence` input to
`requirements reconcile`. It accepts a final-stage, digest-bound legacy TDD
ledger basis when no `--prior-red-proof` is supplied, and rejects the ambiguous
combination. The option is additive and does not change existing red-JUnit
reconciliation callers.

Required core updates:

- `.github/workflows/requirements-evidence.yml` must verify the legacy ledger
  digest, generate the bounded reconciliation input, and forward it only to
  final reconciliation.
- `ci/module-fixture.lock.json` and fixture assertions pin only the merged
  #379 commit `69f075819be5e1ceca1446b026b0417f19e584ca`.
- Workflow regression tests must cover the valid ledger path and stale or
  ambiguous input rejection.
- The runtime-discovery smoke registry must derive the recursive
  `bundle_dependencies` closure of its bounded root module set so newly
  declared modules-side dependencies remain installable in the isolated smoke
  fixture.
- The runtime-proof OpenSpec requirement and evidence mapping must explicitly
  record the legacy migration exception without weakening normal red-JUnit
  proof.

The modules reconciliation code validates the supplied record shape and its
mapping/plan binding, but it cannot read the core repository ledger. Core must
therefore verify that the record's `ledger_digest` equals the committed
`TDD_EVIDENCE.md` bytes before invoking the module.

## Post-Review Revalidation (2026-08-11)

Independent review of the failing-first gate found that a retained red proof was
accepted while inputs pytest actually reads could change after the red source.
Remediation extended `scripts/requirements_proof_provenance.py` to resolve the
complete pytest-determining input set and to fail closed on any input it cannot
read, parse, or statically resolve. Two consequences for this report:

- The gate script is not a declared touchpoint of `git-bound-failing-first-proof`
  in `requirements-evidence.yaml`, so this change's own "changed interface ->
  mapped touchpoint -> exact selector" chain does not cover the file
  implementing the requirement. The correction is drafted in task 3.9 but
  deliberately not applied here: it changes the mapping digest, which is pinned
  in the acceptance record and in two workflow constants that only a
  product-owner run can regenerate.
- The requirement text no longer restates a partial input list. The enumeration
  exists once, in the retained-proof scenario, because the duplicate had already
  drifted behind the implementation.

Validation result remains Pass and impact level remains Medium. No public core
command signature changed, and the resolved proof inputs for this repository are
unchanged, so the hardening rejects evidence that was previously accepted without
widening what a valid red-to-green flow must hold stable.

## Impact Assessment

- **Code Impact:** CI workflow, fixture lock, the internal runtime-discovery
  smoke registry, and the red-proof provenance validator
  `scripts/requirements_proof_provenance.py`; no public core command signature
  changes.
- **Test Impact:** workflow contract coverage and evidence-mapping selector
  coverage require additions.
- **Documentation Impact:** the active change specification and design require
  a narrowly scoped migration exception. No published user documentation is
  affected until the pinned module release is available.
- **Release Impact:** dependency pin update follows the published modules
  release; no separate core version bump is required for this workflow-only
  remediation.

## OpenSpec Validation

- **Command:** `openspec validate requirements-07-runtime-proof-delivery --strict`
- **Status:** Pass
- **Internal Wiki:** no matching `wiki/sources/requirements-07-runtime-proof-delivery.md`
  exists in the sibling internal checkout; record the follow-up rather than
  creating or assuming a mirror update.
