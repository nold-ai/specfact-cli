# Tasks: enterprise-03-aggregation-and-drift-analytics

## 1. Branch and dependency guardrails

- [ ] 1.1 Create dedicated worktree branch `feature/enterprise-03-aggregation-and-drift-analytics` from `dev`.
- [ ] 1.2 Confirm `knowledge-01-distillation-engine` and `enterprise-02-rbac-and-audit-trail` remain the authority for source evidence and audit events.
- [ ] 1.3 Coordinate downstream integration points with future enterprise analytics backends.

## 2. Spec-first and test-first preparation

- [ ] 2.1 Finalize `specs/enterprise-drift-analytics/spec.md` and the `enterprise-audit-trail` delta.
- [ ] 2.2 Write tests for contribution flags, aggregation payload validation, and drift metric calculations.
- [ ] 2.3 Write tests proving analytics summaries can be reconstructed from audit/evidence references.
- [ ] 2.4 Capture failing-first evidence in `TDD_EVIDENCE.md`.

## 3. Implementation

- [ ] 3.1 Implement contribution metadata and aggregation payload builders.
- [ ] 3.2 Implement client-side drift metric calculation helpers.
- [ ] 3.3 Implement local publication/storage of analytics summaries.
- [ ] 3.4 Extend audit-linked evidence references needed for drift reconstruction.

## 4. Validation and documentation

- [ ] 4.1 Re-run tests until all drift-analytics scenarios pass; update `TDD_EVIDENCE.md`.
- [ ] 4.2 Update docs covering contribution flags, drift metrics, and analytics summaries.
- [ ] 4.3 Run `openspec validate enterprise-03-aggregation-and-drift-analytics --strict`.
- [ ] 4.4 Run quality gates for touched scope, including `hatch run format`, `hatch run type-check`, `hatch run lint`, `hatch run contract-test`, `hatch run smart-test`, and fresh `.specfact/code-review.json`.

## 5. Delivery

- [ ] 5.1 Mirror the change into `specfact-cli-internal/wiki/sources/enterprise-03-aggregation-and-drift-analytics.md` and rebuild the internal wiki graph.
- [ ] 5.2 Update `openspec/CHANGE_ORDER.md` with downstream dependency notes.
- [ ] 5.3 Open PR from `feature/enterprise-03-aggregation-and-drift-analytics` to `dev`.
- [ ] 5.4 After merge, remove the worktree branch and prune stale worktree state.
