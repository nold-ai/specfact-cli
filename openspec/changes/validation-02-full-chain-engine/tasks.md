# Tasks: validation-02-full-chain-engine

## Scope rescope — 2026-09-20

Consume current_execution independently from optional chronology. No global graph, full-chain completeness, or historical proof prerequisite for <https://github.com/nold-ai/specfact-cli/issues/740>. Missing mappings remain unassessed coverage, not fabricated completeness. Preserve graph validation for users who request that capability.

This owner-requested scope amendment takes precedence over conflicting default-workflow or dependency wording below. It changes planning only; runtime policy is unchanged. [Replacement policy](../requirements-09-minimal-evidence/proposal.md).

Implementation discipline: use focused regression/reproduction and current-run results. Any task requiring immutable hosted RED, frozen test authoring or approval receipts merely to implement this feature is superseded; tests of an explicitly selected optional seal feature remain in scope.

## 1. Branch and dependency guardrails

- [ ] 1.1 Create dedicated worktree branch `feature/validation-02-full-chain-engine` from `dev` before implementation work: `scripts/worktree.sh create feature/validation-02-full-chain-engine`.
- [ ] 1.2 Verify prerequisite changes are implemented or explicitly accepted as parallel work.
- [ ] 1.3 Reconfirm scope against the validation evidence graph positioning and this proposal.

## 2. Spec-first and test-first preparation

- [ ] 2.1 Finalize `specs/` deltas for all listed capabilities and cross-check scenario completeness.
- [ ] 2.2 Add/update tests mapped to new and modified scenarios.
- [ ] 2.3 Run targeted tests before behavior edits and summarize relevant failures and subsequent passes in concise validation notes with existing local or CI references; no authored TDD ledger is required under the effective lean policy.

## 3. Implementation

- [ ] 3.1 Implement minimal production code required to satisfy the new scenarios.
- [ ] 3.2 Add/update contract decorators and type enforcement on public APIs.
- [ ] 3.3 Update command wiring, adapters, and models required by this change scope only.
- [ ] 3.4 Add code-review evidence as an optional side channel and keep clean-code reporting out of any upstream planning state machine.

## 4. Validation and documentation

- [ ] 4.1 Re-run tests and quality gates until all changed scenarios pass.
- [ ] 4.2 Update user-facing docs and navigation for changed/added commands and workflows.
- [ ] 4.3 Run `openspec validate validation-02-full-chain-engine --strict` and resolve all issues.

## 5. Delivery

- [ ] 5.1 Update `openspec/CHANGE_ORDER.md` status/dependency notes if implementation sequencing changed.
- [ ] 5.2 Open a PR from `feature/validation-02-full-chain-engine` to `dev` with spec/test/code/docs evidence.
