# Tasks: finops-02-budget-approval-gates

## 1. Branch and dependency guardrails

- [ ] 1.1 Create worktree from `origin/dev`: `git worktree add ../specfact-cli-worktrees/feature/finops-02-budget-approval-gates -b feature/finops-02-budget-approval-gates origin/dev` (adjust path per local layout; follow `AGENTS.md`).
- [ ] 1.2 Run `hatch env create` inside the new worktree before implementation.
- [ ] 1.3 Pre-flight: `hatch run smart-test-status`, `hatch run contract-test-status`, `hatch run format` (dry), and `git status` clean; resolve failures before commits/pushes.
- [ ] 1.4 `AGENTS.md` self-check: worktree-only work, no direct commits to `dev`/`main`.
- [ ] 1.5 Confirm `finops-01-telemetry-and-outcomes` remains the authority for evidence schema and outcomes.
- [ ] 1.6 Coordinate with downstream `enterprise-04-budget-governance-and-chargeback`.

## 2. Spec-first and test-first preparation

- [ ] 2.1 Finalize `specs/finops-budget-gates/spec.md` and the `finops-telemetry-outcomes` delta.
- [ ] 2.2 Write budget policy schema tests covering flow caps, project budgets, and approval tiers.
- [ ] 2.3 Write gate tests covering advisory, auto, and approval-required paths.
- [ ] 2.4 Write resume-token and burndown-report tests.
- [ ] 2.5 Capture failing-first evidence in `TDD_EVIDENCE.md`.

## 3. Implementation

- [ ] 3.1 Implement budget policy schema and projected-overage evaluation.
- [ ] 3.2 Implement approval gate responses and resume-token handling.
- [ ] 3.3 Implement burndown reporting from FinOps evidence.
- [ ] 3.4 Extend FinOps evidence to record gate, approval, and wait-state events.

## 4. Validation and documentation

- [ ] 4.1 Re-run tests until all budget-gate scenarios pass; update `TDD_EVIDENCE.md`.
- [ ] 4.2 Update docs covering budget policies, pause/resume, and reporting behavior.
- [ ] 4.3 Run `openspec validate finops-02-budget-approval-gates --strict`.
- [ ] 4.4 Run quality gates for touched scope, including `hatch run format`, `hatch run type-check`, `hatch run lint`, `hatch run contract-test`, `hatch run smart-test`, and fresh `.specfact/code-review.json`.

## 5. Delivery

- [ ] 5.1 Mirror the change into `specfact-cli-internal/wiki/sources/finops-02-budget-approval-gates.md` and rebuild the internal wiki graph.
- [ ] 5.2 Update `openspec/CHANGE_ORDER.md` with downstream dependency notes.
- [ ] 5.3 Open PR from `feature/finops-02-budget-approval-gates` to `dev`.
- [ ] 5.4 After merge to `dev`, from repository root run `openspec archive finops-02-budget-approval-gates` when the change completes.
- [ ] 5.5 After merge, run worktree cleanup: `git worktree remove <path>`, `git branch -d feature/finops-02-budget-approval-gates`, `git worktree prune`, and delete remote branch if your release flow requires (`git push origin --delete feature/finops-02-budget-approval-gates`).
