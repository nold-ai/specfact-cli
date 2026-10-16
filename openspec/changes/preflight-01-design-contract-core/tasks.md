# Tasks: preflight-01-design-contract-core

## Scope rescope — 2026-09-20

Seal, checkpoint, frozen mapping, successor approval, and historical RED/GREEN requirements in this issue apply only when an explicitly selected assurance policy requests them. They are not prerequisites for ordinary implementation, Code Review, release promotion, skill installation, or generated instructions. Keep the internal optional-feature dependency chain and source/signature integrity. Missing optional chronology is not a failed current-execution claim. No runtime policy changes in this planning update.

This owner-requested scope amendment takes precedence over conflicting default-workflow or dependency wording below. It changes planning only; runtime policy is unchanged. [Replacement policy](../requirements-09-minimal-evidence/proposal.md).

Implementation discipline: use focused regression/reproduction and current-run results. Any task requiring immutable hosted RED, frozen test authoring or approval receipts merely to implement this feature is superseded; tests of an explicitly selected optional seal feature remain in scope.

All tasks below are future implementation work. This planning change completes none of them and creates no `TDD_EVIDENCE.md`.

## 1. Dedicated session, worktree, and readiness

- [ ] 1.1 In a dedicated issue-linked session, create `feature/preflight-01-design-contract-core` from current `origin/dev` in a new worktree before any implementation edit.
- [ ] 1.2 Refresh the hierarchy cache and verify the linked issue is open, `Todo`, assigned, correctly parented and labeled, and not already `In Progress`; pause for clarification if concurrent work is possible.
- [ ] 1.3 Verify all native blockers are resolved and revalidate scope against current core/modules OpenSpec artifacts and repository interfaces.

## 2. Specification and failing-first evidence

- [ ] 2.1 Finalize the delta scenarios and exact public interface names for role-classified scope, component ownership, per-input influence/no-impact disposition, risk disposition, execution stages, and Requirements-plan references without widening into CLI, persistence, validators, skills, or adapters.
- [ ] 2.2 Add tests mapped to every contract, influence/no-impact completeness, risk-matrix, planned-to-test-authored Requirements lifecycle, selector reconciliation, implementation-lineage/predecessor seal and monotonic sequence, canonicalization, seal, and verifier scenario.
- [ ] 2.3 Run targeted tests before production edits and summarize meaningful failures briefly using existing local or CI output; no authored TDD ledger is required under the effective lean policy.

## 3. Minimal core implementation

- [ ] 3.1 Implement only the approved reusable contract and result models, including closed scope roles, influence/no-impact dispositions, risk dispositions, verification stages, and immutable implementation-lineage origin/predecessor identities.
- [ ] 3.2 Implement versioned canonicalization and digest behavior proved by the tests.
- [ ] 3.3 Implement the side-effect-free verifier interface, Requirements-plan identity binding, and explicit assurance-limit semantics.

## 4. Passing evidence and quality gates

- [ ] 4.1 Re-run mapped tests and capture passing evidence after implementation.
- [ ] 4.2 Run required format, type, lint, contract, smart-test, test, and SpecFact code-review gates for the touched scope; resolve all findings.
- [ ] 4.3 Run `openspec status --change preflight-01-design-contract-core --json` and `openspec validate preflight-01-design-contract-core --strict`.
- [ ] 4.4 Update documentation and concise validation notes only with observed commands and results.

## 5. Delivery and post-merge cleanup

- [ ] 5.1 Reconfirm issue-approved scope and prepare the downstream interface handoff against the candidate; do not claim it is released yet.
- [ ] 5.2 Open and integrate the reviewed implementation PR to `dev`, then promote through protected `main` and publish the core interface through the existing release workflow after required checks.
- [ ] 5.3 Before archive, verify the released core identity was handed to modules #431 and that modules-owned signing/publication remains assigned to #432; then, from the repository root after merge, run `openspec archive preflight-01-design-contract-core`, update ordering/source mirrors, and remove the dedicated worktree and merged branch.
