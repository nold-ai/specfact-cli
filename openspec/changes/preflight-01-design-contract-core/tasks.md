# Tasks: preflight-01-design-contract-core

All tasks below are future implementation work. This planning change completes none of them and creates no `TDD_EVIDENCE.md`.

## 1. Dedicated session, worktree, and readiness

- [ ] 1.1 In a dedicated issue-linked session, create `feature/preflight-01-design-contract-core` from current `origin/dev` in a new worktree before any implementation edit.
- [ ] 1.2 Refresh the hierarchy cache and verify the linked issue is open, `Todo`, assigned, correctly parented and labeled, and not already `In Progress`; pause for clarification if concurrent work is possible.
- [ ] 1.3 Verify all native blockers are resolved and revalidate scope against current core/modules OpenSpec artifacts and repository interfaces.

## 2. Specification and failing-first evidence

- [ ] 2.1 Finalize the delta scenarios and exact public interface names for role-classified scope, component ownership, risk disposition, execution stages, and Requirements-plan references without widening into CLI, persistence, validators, skills, or adapters.
- [ ] 2.2 Add tests mapped to every contract, risk-matrix, Requirements-reference, canonicalization, seal, and verifier scenario.
- [ ] 2.3 Run the targeted tests before production edits, capture expected failures, and create `TDD_EVIDENCE.md` with the red evidence.

## 3. Minimal core implementation

- [ ] 3.1 Implement only the approved reusable contract and result models, including closed scope roles, risk dispositions, and verification stages.
- [ ] 3.2 Implement versioned canonicalization and digest behavior proved by the tests.
- [ ] 3.3 Implement the side-effect-free verifier interface, Requirements-plan identity binding, and explicit assurance-limit semantics.

## 4. Passing evidence and quality gates

- [ ] 4.1 Re-run mapped tests and capture passing evidence after implementation.
- [ ] 4.2 Run required format, type, lint, contract, smart-test, test, and SpecFact code-review gates for the touched scope; resolve all findings.
- [ ] 4.3 Run `openspec status --change preflight-01-design-contract-core --json` and `openspec validate preflight-01-design-contract-core --strict`.
- [ ] 4.4 Update documentation and `TDD_EVIDENCE.md` only with observed commands and results.

## 5. Delivery and post-merge cleanup

- [ ] 5.1 Reconfirm the diff contains only issue-approved scope and that downstream modules contracts reference the released core interface identity.
- [ ] 5.2 Open the implementation PR to `dev` as the final pre-merge task, linking the issue and evidence.
- [ ] 5.3 After merge, run `openspec archive preflight-01-design-contract-core`, update ordering/source mirrors, and remove the dedicated worktree and merged branch.
