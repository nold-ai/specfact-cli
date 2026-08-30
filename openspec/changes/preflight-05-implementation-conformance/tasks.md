# Tasks: preflight-05-implementation-conformance (core contracts)

All tasks below are future implementation work. This planning change completes none of them and creates no `TDD_EVIDENCE.md`.

## 1. Dedicated session, worktree, and readiness

- [ ] 1.1 In a dedicated issue-linked session, create `feature/preflight-05-implementation-conformance` from current `origin/dev` in a new core worktree before any implementation edit.
- [ ] 1.2 Refresh hierarchy metadata and verify this issue is correctly parented/labeled/assigned, `Todo`, blocked by the stable preflight release, blocks paired modules #434, and is not active in another session.
- [ ] 1.3 Revalidate the released preflight seal and traceability interfaces against current core/modules reality.

## 2. Specification and failing-first evidence

- [ ] 2.1 Finalize snapshot kinds, complete path manifest, obligation mapping, local checkpoint authority, immutable conformance, finding, result, and verifier interfaces without adding extraction or CLI behavior.
- [ ] 2.2 Add tests mapped to every worktree/index/range identity, including local checkpoint verification without a delivery-target input and final-range rejection without exact authoritative delivery-head identity; implementation-lineage-origin equality across successor seals; canonical latest-seal tip/sequence/chain verification; origin-to-head ancestry; authority separation; path transitions; role-independent public-interface observation completeness for every policy-classified interface-capable governed path; checkpoint-subset and exhaustive final-obligation closure; protected-CI producer authorization and exact-range provenance; finding-class/precedence (including the reconciled semantic `violated` scenario); stale-seal; evidence; and assurance-limit scenarios.
- [ ] 2.3 Run targeted tests before production edits and record failing-first results in a newly created `TDD_EVIDENCE.md`.

## 3. Minimal core implementation

- [ ] 3.1 Implement the normalized implementation snapshot and evidence-reference models for worktree, index, and range identities.
- [ ] 3.2 Implement obligation mapping, `DevelopmentCheckpointResult`, `ImplementationConformanceResult`, and closed finding contracts.
- [ ] 3.3 Implement the side-effect-free verifier over supplied upstream verification inputs, obligations, and evidence, preserving explicit assurance limits without applicability or policy orchestration.
- [ ] 3.4 Implement result validation that rejects local-authority promotion and enforces deterministic status aggregation.

## 4. Passing evidence and quality gates

- [ ] 4.1 Re-run mapped tests and capture passing evidence after implementation.
- [ ] 4.2 Run required format, type, lint, contract, smart-test, test, and SpecFact code-review gates; resolve all findings.
- [ ] 4.3 Run `openspec status --change preflight-05-implementation-conformance --json` and `openspec validate preflight-05-implementation-conformance --strict`.
- [ ] 4.4 Update evidence/docs only with observed results and verify no modules runtime behavior entered core.

## 5. Delivery and post-merge cleanup

- [ ] 5.1 Hand the exact released core implementation-assurance interface identity to paired modules #434 before #251/#253/#433 begin.
- [ ] 5.2 Open the implementation PR to `dev` as the final pre-merge task, linking the paired modules issue and evidence.
- [ ] 5.3 Before archive, verify the released core identity was handed to modules #434 and that modules-owned signing/stable publication remains assigned there; then, from the repository root after merge, run `openspec archive preflight-05-implementation-conformance`, update ordering/source mirrors, and remove the dedicated worktree and merged branch.
