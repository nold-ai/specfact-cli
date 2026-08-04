# Change Validation Report: requirements-07-runtime-proof-delivery

**Validation Date:** 2026-08-05 (Europe/Berlin)
**Change Proposal:** [proposal.md](./proposal.md)
**Validation Method:** dependency dry-run using a temporary workspace and the
current source of modules PR #379.

## Executive Summary

- Breaking Changes: 0 detected
- Dependent Files: 6 direct core integration files
- Impact Level: Medium
- Validation Result: Pass with a published-fixture dependency
- User Decision: Prepare the core integration; do not pin a mutable module
  branch.

## Dependency Analysis

Modules PR #379 adds an optional `--legacy-tdd-evidence` input to
`requirements reconcile`. It accepts a final-stage, digest-bound legacy TDD
ledger basis when no `--prior-red-proof` is supplied, and rejects the ambiguous
combination. The option is additive and does not change existing red-JUnit
reconciliation callers.

Critical core updates remain:

- `.github/workflows/requirements-evidence.yml` must verify the legacy ledger
  digest, generate the bounded reconciliation input, and forward it only to
  final reconciliation.
- `ci/module-fixture.lock.json` and fixture assertions must move only to the
  signed, published #379 commit once available.
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

## Impact Assessment

- **Code Impact:** CI workflow, fixture lock, and the internal
  runtime-discovery smoke registry; no public core command signature changes.
- **Test Impact:** workflow contract coverage and evidence-mapping selector
  coverage require additions.
- **Documentation Impact:** the active change specification and design require
  a narrowly scoped migration exception. No published user documentation is
  affected until the pinned module release is available.
- **Release Impact:** dependency pin update after the modules release; no core
  version bump while preparation remains unshipped.

## OpenSpec Validation

- **Command:** `openspec validate requirements-07-runtime-proof-delivery --strict`
- **Status:** Pass
- **Internal Wiki:** no matching `wiki/sources/requirements-07-runtime-proof-delivery.md`
  exists in the sibling internal checkout; record the follow-up rather than
  creating or assuming a mirror update.
