# Tasks: fix-release-promotion-requirements-parity

## 1. Governance and specification

- [x] 1.1 Refresh `origin/dev`, issue #692 metadata, and the GitHub hierarchy cache.
- [x] 1.2 Define the exact repository/ref/commit/tree/ancestry and prior-evidence
  release-promotion boundary.
- [x] 1.3 Validate the OpenSpec change strictly before implementation.

## 2. Tests first

- [x] 2.1 Add mapped validator and workflow regressions for exact promotion
  acceptance; lookalike, stale, spoofed, ambiguous, expired, and digest-tampered
  rejection; and producer/consumer/final independent validation.
- [x] 2.2 Run the focused selectors against unmodified production code and retain
  failing-before evidence.
- [x] 2.3 Obtain acceptance for the stable test-authored mapping before the
  implementation commit.

## 3. Minimal implementation

- [x] 3.1 Add one canonical promotion-reuse validator for event, commit/tree,
  source-pull, check/run, artifact, report, plan, and JUnit bindings.
- [x] 3.2 Require producer, consumer, and final to fetch and independently
  validate exact live evidence and byte-identical promotion attestations.
- [x] 3.3 Permit aggregate planning validation only when the separate promotion
  attestation passes; do not claim current aggregate selector execution.
- [x] 3.4 Leave trusted main-relative inputs, every ordinary pull request, and
  every independent authority/release gate unchanged.

## 4. Verification and delivery

- [x] 4.1 Run focused legitimate and bypass controls, full workflow tests, strict
  OpenSpec validation, workflow lint, and `git diff --check`.
- [x] 4.2 Run independent security-boundary and bypass/regression review; resolve
  all P0/P1/P2 findings and disposition warnings.
- [x] 4.3 Review README, `docs/`, the docs landing page, and navigation; record why
  this internal release-control correction requires no public documentation edit.
- [x] 4.4 Run strict module-signature verification; do not re-sign or bump a module
  because no signed module asset or manifest changes.
- [x] 4.5 Validate the existing unreleased `0.55.4` four-source version and
  changelog bundle against `origin/dev`; do not consume `0.55.5` for a follow-up
  required to make the same release promotable.
- [x] 4.6 Generate a fresh `.specfact/code-review.json`, resolve every finding or
  document an approved narrow exception, and record the exact review evidence.
- [ ] 4.7 Push an issue-linked pull request to `dev`, obtain all required checks,
  and merge only under repository policy.
- [ ] 4.8 Re-run PR #691 at the new exact `dev` head and verify Requirements,
  security, release, review, and authority gates before promotion.
