# Tasks: ai-integration-03-instruction-files

All tasks below are future implementation work. This rescope completes none of them and creates no generated instruction or `TDD_EVIDENCE.md`.

## 1. Dedicated session, worktree, and readiness

- [ ] 1.1 In a dedicated issue-linked session, create `feature/ai-integration-03-instruction-files` from current `origin/dev` in a new core worktree before any implementation edit.
- [ ] 1.2 Refresh hierarchy metadata and verify #253 retains parent #372, is blocked by #251, has complete labels/project/assignee, and is not concurrently `In Progress`.
- [ ] 1.3 Verify #251's released inventory/descriptor contract and current OpenSpec/Spec Kit primary-source behavior before fixing the target matrix.

## 2. Specification and failing-first evidence

- [ ] 2.1 Finalize gate fields, managed markers, inventories, OpenSpec ordering, Spec Kit extension compatibility, and invocation resolution without validator or adapter packaging scope.
- [ ] 2.2 Add tests mapped to idempotency, malformed markers, user-content preservation, OpenSpec/Spec Kit ordering, and harness-native invocation fixtures.
- [ ] 2.3 Run targeted tests before production edits and record failing-first results in a newly created `TDD_EVIDENCE.md`.

## 3. Minimal instruction implementation

- [ ] 3.1 Implement previewable managed-section generation for AGENTS.md and the approved core-owned target files.
- [ ] 3.2 Implement installed-metadata invocation resolution and safe inventory-backed update/removal.
- [ ] 3.3 Implement OpenSpec and Spec Kit ordering references while respecting each upstream tool's context ownership.
- [ ] 3.4 Keep detailed preflight workflow content, validators, and external adapter packages out of core.

## 4. Passing evidence and quality gates

- [ ] 4.1 Re-run mapped tests and fixture matrices and capture passing evidence after implementation.
- [ ] 4.2 Run required format, type, lint, contract, smart-test, test, and SpecFact code-review gates; resolve all findings.
- [ ] 4.3 Run `openspec status --change ai-integration-03-instruction-files --json` and `openspec validate ai-integration-03-instruction-files --strict`.
- [ ] 4.4 Document preview, ownership markers, uninstall, OpenSpec/Spec Kit ordering, and limits using observed behavior.

## 5. Delivery and post-merge cleanup

- [ ] 5.1 Hand the exact managed-section and invocation contract to modules `preflight-04-harness-adapters`.
- [ ] 5.2 Open the implementation PR to `dev` as the final pre-merge task, linking #253, #251, and downstream adapter issue.
- [ ] 5.3 After merge, run `openspec archive ai-integration-03-instruction-files`, update ordering/wiki source state, and remove the dedicated worktree and merged branch.
