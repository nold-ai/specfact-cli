# Tasks: architecture-02-well-architected-review

## 1. Branch and dependency guardrails

- [ ] 1.1 Create dedicated worktree branch `feature/architecture-02-well-architected-review` from `origin/dev` per `AGENTS.md` (git worktree add … `-b` … `origin/dev`).
- [ ] 1.2 Run `hatch env create` in that worktree to bootstrap the Hatch environment before implementation.
- [ ] 1.3 Run repository pre-flight checks from `AGENTS.md`: `hatch run smart-test-status`, `hatch run contract-test-status`, and confirm a clean git status / up-to-date branch as applicable.
- [ ] 1.4 Confirm `architecture-01-solution-layer`, `review-finding-model`, and `review-report-model` remain the source of truth for shared contracts.
- [ ] 1.5 Coordinate with the modules-side companion `architecture-02-module-well-architected`.

## 2. Spec-first and test-first preparation

- [ ] 2.1 Finalize `specs/architecture-review/spec.md` and the `solution-architecture` delta.
- [ ] 2.2 Write tests for architecture finding categories and deterministic severity/rule-id mapping.
- [ ] 2.3 Write interface-diff tests covering breaking, additive, and non-breaking changes.
- [ ] 2.4 Write ADR traceability tests that fail when required links are missing.
- [ ] 2.5 Capture failing-first evidence in `TDD_EVIDENCE.md`.

## 3. Implementation

- [ ] 3.1 Implement the architecture review finding model and scorer in core.
- [ ] 3.2 Implement `specfact architecture diff --since <ref>` with deterministic classification output.
- [ ] 3.3 Extend the solution-architecture layer to emit ADR-linked review evidence.
- [ ] 3.4 Add shared review-report envelope integration and policy hooks for architecture findings.

## 4. Validation and documentation

- [ ] 4.1 Re-run tests until all architecture scenarios pass; update `TDD_EVIDENCE.md`.
- [ ] 4.2 Update architecture and review docs, including interface-diff usage and ADR requirements.
- [ ] 4.3 Run `openspec validate architecture-02-well-architected-review --strict`.
- [ ] 4.4 Run quality gates for touched scope, including `hatch run format`, `hatch run type-check`, `hatch run lint`, `hatch run contract-test`, `hatch run smart-test`, and fresh `.specfact/code-review.json`.

## 5. Delivery

- [ ] 5.1 Mirror the change into `specfact-cli-internal/wiki/sources/architecture-02-well-architected-review.md` and rebuild the internal wiki graph.
- [ ] 5.2 Update `openspec/CHANGE_ORDER.md` with downstream dependency notes.
- [ ] 5.3 Open PR from `feature/architecture-02-well-architected-review` to `dev`.
- [ ] 5.4 After merge validation passes, from **repository root** run `openspec archive architecture-02-well-architected-review`
  (canonical `/opsx:archive` lifecycle: merge deltas into `openspec/specs/`, move change under `openspec/changes/archive/`,
  module signing/cleanup as configured). **Do not** manually `mv` folders into `openspec/changes/archive/`.
- [ ] 5.5 After archive completes, remove the worktree branch and prune stale worktree state.
