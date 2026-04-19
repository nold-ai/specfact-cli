# Tasks: enterprise-02-rbac-and-audit-trail

## 1. Branch and dependency guardrails

- [ ] 1.1 Create dedicated worktree branch `feature/enterprise-02-rbac-and-audit-trail` from `origin/dev` (per `AGENTS.md`).
- [ ] 1.2 Run `hatch env create` in the worktree before any implementation.
- [ ] 1.3 Run pre-flight checks: `hatch run smart-test-status` and `hatch run contract-test-status`.
- [ ] 1.4 Confirm `enterprise-01-policy-resolution-extension` remains the authority for enterprise precedence and provenance.
- [ ] 1.5 Coordinate with module-side `enterprise-02-module-audit-client` and confirm module readiness timelines.

## 2. Spec-first and test-first preparation

- [ ] 2.1 Finalize `specs/enterprise-audit-trail/spec.md` and the `enterprise-policy-resolution` delta.
- [ ] 2.2 Write schema tests for role values and signed audit-event fields.
- [ ] 2.3 Write policy-linkage tests proving resolved values can reference audit events.
- [ ] 2.4 Capture failing-first evidence in `TDD_EVIDENCE.md`.

## 3. Implementation

- [ ] 3.1 Implement the enterprise role vocabulary and validation helpers.
- [ ] 3.2 Implement append-only signed audit-event schema and local persistence.
- [ ] 3.3 Link enterprise rule pushes, overrides, and approvals to audit-event ids.
- [ ] 3.4 Add inspection/documentation support for enterprise audit history.

## 4. Validation and documentation

- [ ] 4.1 Re-run tests until all audit-trail scenarios pass; update `TDD_EVIDENCE.md`.
- [ ] 4.2 Update docs covering roles, audited actions, and local persistence behavior.
- [ ] 4.3 Run `openspec validate enterprise-02-rbac-and-audit-trail --strict`.
- [ ] 4.4 Run quality gates for touched scope, including `hatch run format`, `hatch run type-check`, `hatch run lint`, `hatch run contract-test`, `hatch run smart-test`, and fresh `.specfact/code-review.json`.

## 5. Delivery

- [ ] 5.1 Mirror the change into `specfact-cli-internal/wiki/sources/enterprise-02-rbac-and-audit-trail.md` and rebuild the internal wiki graph.
- [ ] 5.2 Update `openspec/CHANGE_ORDER.md` with downstream dependency notes.
- [ ] 5.3 Open PR from `feature/enterprise-02-rbac-and-audit-trail` to `dev`.
- [ ] 5.4 After merge, remove the worktree branch and prune stale worktree state.
- [ ] 5.5 After merge to `dev`, from repository root run `openspec archive enterprise-02-rbac-and-audit-trail` (required closeout; do not manually move change folders under `openspec/changes/archive/`).
