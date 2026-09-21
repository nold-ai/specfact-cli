# Tasks

Specs precede tests; capture failing tests before changing the workflow.

## 1. Prepare

- [x] 1.1 Create an isolated worktree from origin/dev and initialize its environment.
- [x] 1.2 Confirm issue #745, parent #366, project assignment, and no prerequisite blockers.
- [x] 1.3 Define the planning-only boundary and retain implementation/promotion restrictions.

## 2. Reproduce and fix

- [ ] 2.1 Add behavioral tests of actual workflow shell selection and record failing evidence.
- [ ] 2.2 Guard implementation review selection above planned maturity across all stages.
- [ ] 2.3 Run affected workflow tests, lint, and repository-required checks; record results.

## 3. Review and deliver

- [ ] 3.1 Review trust boundaries and documentation impact; synchronize the internal wiki summary.
- [ ] 3.2 Commit signed changes, push, and open a prerequisite PR to dev linked to #745.
- [ ] 3.3 After authorized merge, refresh dependent planning PR #741 and verify remote gates.

## Post-merge

- [ ] Archive with `openspec archive fix-planning-evidence-multichange` after delivery, then remove the isolated worktree.
