# Tasks: code-review-zero-findings

## 1. Branch and scope guardrails

- [x] 1.1 Continue implementation in dedicated worktree branch `bugfix/code-review-zero-findings`.
- [x] 1.2 Reconstruct missing OpenSpec artifacts for the active remediation branch.
- [x] 1.3 Capture the pre-fix failing baseline in `TDD_EVIDENCE.md`.

## 2. Spec-first and test-first preparation

- [x] 2.1 Add a spec delta for the dogfood zero-findings scenario.
- [x] 2.2 Add the dogfood self-review tests.
- [x] 2.3 Record failing-first evidence before additional production fixes.

## 3. Implementation

- [ ] 3.1 Resolve branch-local type errors and remaining remediation regressions in touched files.
- [ ] 3.2 Continue reducing `reportUnknownMemberType`, contract, and clean-code findings in the branch scope.
- [ ] 3.3 Keep the branch aligned with the dogfood review success criteria while avoiding unrelated code churn.

## 4. Validation

- [ ] 4.1 Re-run targeted analyzers/tests for the touched files and update `TDD_EVIDENCE.md`.
- [ ] 4.2 Run the dogfood review command in a branch environment that exposes `specfact code review run`.
- [ ] 4.3 Confirm post-fix evidence reaches `overall_verdict: PASS` with zero findings for the tracked categories.

## 5. Delivery

- [ ] 5.1 Keep `openspec/CHANGE_ORDER.md` current with this change status.
- [ ] 5.2 Prepare the branch for commit/PR once the validation evidence is complete.
