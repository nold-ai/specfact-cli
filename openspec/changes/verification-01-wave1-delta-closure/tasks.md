## 1. Git Workflow and Scope Lock

- [ ] 1.1 Create worktree branch `feature/verification-01-wave1-delta-closure` from `origin/dev` and run all implementation steps in that worktree.
- [x] 1.2 Confirm this change only covers Wave 1 delta-closure gaps (bundle-mapper wiring, patch-mode behavior completion, docs/changelog parity).

## 2. Spec and Validation Baseline

- [x] 2.1 Validate OpenSpec change artifacts: `openspec validate verification-01-wave1-delta-closure --strict`.
- [x] 2.2 Produce/update `openspec/changes/verification-01-wave1-delta-closure/CHANGE_VALIDATION.md` with dependency and breaking-change analysis.

## 3. Tests First (TDD Hard Gate)

- [x] 3.1 Add/extend tests for bundle-mapper runtime hook behavior in backlog refine/import (`--auto-bundle` confidence routing and user fallback behavior).
- [x] 3.2 Add/extend tests for patch-mode local apply and upstream write orchestration (confirmation gate + idempotency behavior).
- [x] 3.3 Add/extend docs/changelog parity tests or lint guards where applicable.
- [x] 3.4 Run targeted tests and capture a failing pre-implementation run in `TDD_EVIDENCE.md`.

## 4. Implement Delta Scope

- [x] 4.1 Implement bundle-mapper hook wiring for backlog refine/import runtime paths.
- [x] 4.2 Implement patch-mode local apply semantics and explicit upstream write path aligned with acceptance criteria.
- [x] 4.3 Update docs and changelog to match actual shipped command behavior and remove duplicate release sections.

## 5. Verify and Quality Gates

- [x] 5.1 Re-run targeted tests and capture passing post-implementation evidence in `TDD_EVIDENCE.md`.
- [ ] 5.2 Run quality gates in order: `hatch run format`, `hatch run type-check`, `hatch run lint`, `hatch run yaml-lint`, `hatch run contract-test`, `hatch run smart-test`.
- [x] 5.3 Re-run `openspec validate verification-01-wave1-delta-closure --strict` and ensure no errors.

## 6. Sync and Delivery

- [ ] 6.1 Sync proposal updates to GitHub issue in `nold-ai/specfact-cli` and ensure required labels (`enhancement`, `openspec`, `change-proposal`).
- [ ] 6.2 Update `openspec/CHANGE_ORDER.md` entry status/metadata for this change.
- [ ] 6.3 Open PR to `dev` with validation evidence and test results.
