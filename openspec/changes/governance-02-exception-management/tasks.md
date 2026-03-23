# Tasks: governance-02-exception-management

## 1. Branch and dependency guardrails

- [ ] 1.1 Create dedicated worktree branch `feature/governance-02-exception-management` from `dev` before implementation work: `scripts/worktree.sh create feature/governance-02-exception-management`.
- [ ] 1.2 Verify prerequisite changes are implemented or explicitly accepted as parallel work.
- [ ] 1.3 Reconfirm scope against the 2026-02-15 architecture integration plan and this proposal.
- [ ] 1.4 Confirm exception-scope ownership boundaries per `openspec/CHANGE_ORDER.md` and avoid schema-envelope changes owned by governance-01.

## 2. Spec-first and test-first preparation

- [ ] 2.1 Finalize `specs/` deltas for all listed capabilities and cross-check scenario completeness.
- [ ] 2.2 Add/update tests mapped to new and modified scenarios.
- [ ] 2.3 Run targeted tests to capture failing-first behavior and record results in `TDD_EVIDENCE.md`.

## 3. Implementation

- [ ] 3.1 Implement minimal production code required to satisfy the new scenarios.
- [ ] 3.2 Add/update contract decorators and type enforcement on public APIs.
- [ ] 3.3 Update command wiring, adapters, and models required by this change scope only.
- [ ] 3.4 Keep exception scope keyed by policy rule ID (for example `clean-code-principles/<rule-id>`) and avoid adding a separate clean-code-principle exception model.

## 4. Validation and documentation

- [ ] 4.1 Re-run tests and quality gates until all changed scenarios pass.
- [ ] 4.2 Update user-facing docs and navigation for changed/added commands and workflows.
- [ ] 4.3 Run `openspec validate governance-02-exception-management --strict` and resolve all issues.

## 5. Delivery

- [ ] 5.1 Update `openspec/CHANGE_ORDER.md` status/dependency notes if implementation sequencing changed.
- [ ] 5.2 Open a PR from `feature/governance-02-exception-management` to `dev` with spec/test/code/docs evidence.
