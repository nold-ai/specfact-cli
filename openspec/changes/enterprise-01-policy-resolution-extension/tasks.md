# Tasks: enterprise-01-policy-resolution-extension

## 1. Branch and dependency guardrails

- [ ] 1.1 Create dedicated worktree branch `feature/enterprise-01-policy-resolution-extension` from `dev`.
- [ ] 1.2 Confirm `profile-01-config-layering` and `policy-engine` remain the authority for local resolution semantics.
- [ ] 1.3 Coordinate with module-side `enterprise-01-module-policy-client`.

## 2. Spec-first and test-first preparation

- [ ] 2.1 Finalize `specs/enterprise-policy-resolution/spec.md` and the `profile-config-layering` delta.
- [ ] 2.2 Write resolution-order tests covering org mandatory, team advisory, CLI, project, profile, and built-in fallback layers.
- [ ] 2.3 Write signature/provenance metadata validation tests.
- [ ] 2.4 Capture failing-first evidence in `TDD_EVIDENCE.md`.

## 3. Implementation

- [ ] 3.1 Implement enterprise-aware resolution ordering and detection.
- [ ] 3.2 Implement pushed-rule metadata handling and validation.
- [ ] 3.3 Add resolution inspection support for enterprise-derived values.
- [ ] 3.4 Ensure local-only users continue to resolve policies without enterprise dependencies.

## 4. Validation and documentation

- [ ] 4.1 Re-run tests until all enterprise resolution scenarios pass; update `TDD_EVIDENCE.md`.
- [ ] 4.2 Update docs covering precedence, override rules, and enterprise no-op behavior.
- [ ] 4.3 Run `openspec validate enterprise-01-policy-resolution-extension --strict`.
- [ ] 4.4 Run quality gates for touched scope, including `hatch run format`, `hatch run type-check`, `hatch run lint`, `hatch run contract-test`, `hatch run smart-test`, and fresh `.specfact/code-review.json`.

## 5. Delivery

- [ ] 5.1 Mirror the change into `specfact-cli-internal/wiki/sources/enterprise-01-policy-resolution-extension.md` and rebuild the internal wiki graph.
- [ ] 5.2 Update `openspec/CHANGE_ORDER.md` with downstream dependency notes.
- [ ] 5.3 Open PR from `feature/enterprise-01-policy-resolution-extension` to `dev`.
- [ ] 5.4 After merge, remove the worktree branch and prune stale worktree state.
