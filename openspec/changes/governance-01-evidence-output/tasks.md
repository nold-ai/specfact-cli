# Tasks: governance-01-evidence-output

## Scope rescope — 2026-09-20

Emit compact current-run observations and artifact references; historical chronology is separate and optional. Do not require a RED ledger, seal lineage, or the complete validation graph just to record lean CI results. Existing graph-output integration remains this issue's scope; <https://github.com/nold-ai/specfact-cli/issues/740> must not depend on its delivery.

This owner-requested scope amendment takes precedence over conflicting default-workflow or dependency wording below. It changes planning only; runtime policy is unchanged. [Replacement policy](../requirements-09-minimal-evidence/proposal.md).

Implementation discipline: use focused regression/reproduction and current-run results. Any task requiring immutable hosted RED, frozen test authoring or approval receipts merely to implement this feature is superseded; tests of an explicitly selected optional seal feature remain in scope.

## 1. Branch and dependency guardrails

- [ ] 1.1 Create dedicated worktree branch `feature/governance-01-evidence-output` from `dev` before implementation work: `scripts/worktree.sh create feature/governance-01-evidence-output`.
- [ ] 1.2 Verify prerequisite changes are implemented or explicitly accepted as parallel work.
- [ ] 1.3 Reconfirm scope against the 2026-02-15 architecture integration plan and this proposal.
- [ ] 1.4 Confirm governance-01 ownership of evidence envelope/schema per `openspec/CHANGE_ORDER.md` before modifying shared outputs.

## 2. Spec-first and test-first preparation

- [ ] 2.1 Finalize `specs/` deltas for all listed capabilities and cross-check scenario completeness.
- [ ] 2.2 Add/update tests mapped to new and modified scenarios.
- [ ] 2.3 Run targeted tests to capture failing-first behavior and record results in `TDD_EVIDENCE.md`.

## 3. Implementation

- [ ] 3.1 Implement minimal production code required to satisfy the new scenarios.
- [ ] 3.2 Add/update contract decorators and type enforcement on public APIs.
- [ ] 3.3 Add the core envelope models and deterministic verdict derivation; do not add command wiring, emitters, or persistence.
- [ ] 3.4 Keep clean-code evidence as a sibling `code_quality` section in the envelope rather than adding a new validation layer.

## 4. Validation and documentation

- [ ] 4.1 Re-run tests and quality gates until all changed scenarios pass.
- [ ] 4.2 Update user-facing docs and navigation for changed/added commands and workflows.
- [ ] 4.3 Run `openspec validate governance-01-evidence-output --strict` and resolve all issues.

## 5. Delivery

- [ ] 5.1 Update `openspec/CHANGE_ORDER.md` status/dependency notes if implementation sequencing changed.
- [ ] 5.2 Open a PR from `feature/governance-01-evidence-output` to `dev` with spec/test/code/docs evidence.
