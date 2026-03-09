# Tasks: module-migration-08-release-suite-stabilization

## 1. Baseline and classification

- [x] 1.1 Capture representative failing unit/integration/E2E commands and summarize root-cause buckets
- [x] 1.2 Distinguish stale test ownership issues from genuine core runtime regressions
- [x] 1.3 Exclude unrelated failures not caused by post-migration core/runtime drift

## 2. Spec and failing tests first

- [x] 2.1 Add spec delta for residual release-suite stabilization behavior
- [x] 2.2 Reproduce representative failures and record pre-fix evidence in `TDD_EVIDENCE.md`

## 3. Implementation

- [x] 3.1 Update stale tests to grouped command and lean-core ownership semantics
- [x] 3.2 Remove or rewrite tests that still depend on extracted in-core bundle paths
- [x] 3.3 Fix genuine core regressions exposed by the failing suites
- [x] 3.4 Harden deterministic signing and installer fixtures where needed
- [x] 3.5 Capture post-fix evidence for targeted buckets and wider reruns

## 4. Validation

- [x] 4.1 Run targeted unit buckets for command topology, init, suggestions, and shim behavior
- [x] 4.2 Run targeted integration buckets for grouped commands and retained core workflows
- [x] 4.3 Run targeted E2E buckets that still belong to core runtime ownership
- [x] 4.4 Re-run broader unit/integration suites or equivalent release confidence subset

## 5. Closure

- [x] 5.1 Update CHANGELOG or release notes only if user-facing behavior changed beyond test expectations
- [x] 5.2 Document residual follow-ups if any failing tests belong in `specfact-cli-modules`
