# Tasks: enterprise-04-budget-governance-and-chargeback

## 1. Branch and dependency guardrails

- [ ] 1.1 Create dedicated worktree branch `feature/enterprise-04-budget-governance-and-chargeback` from `dev`.
- [ ] 1.2 Confirm `finops-02-budget-approval-gates` remains the authority for local budget gate semantics.
- [ ] 1.3 Coordinate with enterprise policy/audit owners and future reporting backends.

## 2. Spec-first and test-first preparation

- [ ] 2.1 Finalize `specs/enterprise-chargeback/spec.md` and the `finops-budget-gates` delta.
- [ ] 2.2 Write tests for enterprise approval-routing metadata and fallback behavior.
- [ ] 2.3 Write tests for chargeback identifiers, report aggregation, and audit linkage.
- [ ] 2.4 Capture failing-first evidence in `TDD_EVIDENCE.md`.

## 3. Implementation

- [ ] 3.1 Implement enterprise routing metadata and validation for budget approvals.
- [ ] 3.2 Implement chargeback identifiers and reporting payloads.
- [ ] 3.3 Extend FinOps budget-gate evidence with enterprise approval and attribution fields.
- [ ] 3.4 Extend audit integration for budget approvals and chargeback changes.

## 4. Validation and documentation

- [ ] 4.1 Re-run tests until all enterprise budget-governance scenarios pass; update `TDD_EVIDENCE.md`.
- [ ] 4.2 Update docs covering enterprise approval routing, team attribution, and chargeback reports.
- [ ] 4.3 Run `openspec validate enterprise-04-budget-governance-and-chargeback --strict`.
- [ ] 4.4 Run quality gates for touched scope, including `hatch run format`, `hatch run type-check`, `hatch run lint`, `hatch run contract-test`, `hatch run smart-test`, and fresh `.specfact/code-review.json`.

## 5. Delivery

- [ ] 5.1 Mirror the change into `specfact-cli-internal/wiki/sources/enterprise-04-budget-governance-and-chargeback.md` and rebuild the internal wiki graph.
- [ ] 5.2 Update `openspec/CHANGE_ORDER.md` with downstream dependency notes.
- [ ] 5.3 Open PR from `feature/enterprise-04-budget-governance-and-chargeback` to `dev`.
- [ ] 5.4 After merge, remove the worktree branch and prune stale worktree state.
