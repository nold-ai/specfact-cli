# Tasks: finops-01-telemetry-and-outcomes

## 1. Branch and dependency guardrails

- [ ] 1.1 Create dedicated worktree branch `feature/finops-01-telemetry-and-outcomes` from `origin/dev` (per `AGENTS.md`; use `git worktree add` … `origin/dev`, not a stale local `dev` tip).
- [ ] 1.2 Run `hatch env create` in the worktree to bootstrap dependencies before implementation.
- [ ] 1.3 Pre-flight status: CI parity for the base commit, dependency snapshot / environment health (`hatch run smart-test-status`, `hatch run contract-test-status` where applicable), and workspace cleanliness per team practice.
- [ ] 1.4 `AGENTS.md` policy self-check: confirm implementation happens only from the dedicated worktree.
- [ ] 1.5 Confirm `telemetry-01-opentelemetry-default-on` remains the authority for redacted emitter behavior.
- [ ] 1.6 Coordinate with module-side `finops-01-module-cost-outcome` and downstream `finops-02-budget-approval-gates`.

## 2. Spec-first and test-first preparation

- [ ] 2.1 Finalize `specs/finops-telemetry-outcomes/spec.md` and the `telemetry-otel` delta.
- [ ] 2.2 Write schema tests for required fields, outcome enum values, and cost/token validation.
- [ ] 2.3 Write efficiency ratio tests covering zero-token and mixed-cost cases.
- [ ] 2.4 Write telemetry extension tests proving prompt/content redaction still holds.
- [ ] 2.5 Capture failing-first evidence in `TDD_EVIDENCE.md`.

## 3. Implementation

- [ ] 3.1 Implement the FinOps session evidence schema and shared outcome enum in core.
- [ ] 3.2 Implement efficiency-ratio calculation and validation helpers.
- [ ] 3.3 Extend telemetry emission paths to carry safe FinOps metadata.
- [ ] 3.4 Wire the schema into evidence and distillation entry points.

## 4. Validation and documentation

- [ ] 4.1 Re-run tests until all FinOps scenarios pass; update `TDD_EVIDENCE.md`.
- [ ] 4.2 Update docs covering telemetry, evidence, and outcome vocabulary.
- [ ] 4.3 Run `openspec validate finops-01-telemetry-and-outcomes --strict`.
- [ ] 4.4 Run quality gates for touched scope, including `hatch run format`, `hatch run type-check`, `hatch run lint`, `hatch run contract-test`, `hatch run smart-test`, and fresh `.specfact/code-review.json`.

## 5. Delivery

- [ ] 5.1 Mirror the change into `specfact-cli-internal/wiki/sources/finops-01-telemetry-and-outcomes.md` and rebuild the internal wiki graph.
- [ ] 5.2 Update `openspec/CHANGE_ORDER.md` with downstream dependency notes.
- [ ] 5.3 Open PR from `feature/finops-01-telemetry-and-outcomes` to `dev`.
- [ ] 5.4 After merge to `dev`, from repository root run `openspec archive finops-01-telemetry-and-outcomes` (do not manually move change folders).
- [ ] 5.5 After merge, remove the worktree branch and prune stale worktree state (`git worktree remove`, `git branch -d`, `git worktree prune` per `AGENTS.md`).
