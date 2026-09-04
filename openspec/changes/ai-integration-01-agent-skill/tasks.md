# Tasks: ai-integration-01-agent-skill

All tasks below are future implementation work. This rescope completes none of them and creates no skill/export or `TDD_EVIDENCE.md`.

## 1. Dedicated session, worktree, and readiness

- [ ] 1.1 In a dedicated issue-linked session, create `feature/ai-integration-01-agent-skill` from current `origin/dev` in a new core worktree before any implementation edit.
- [ ] 1.2 Refresh hierarchy metadata and verify #251 retains parent #372, complete labels/project/assignee, the signed modules #434 blocker, and no concurrent `In Progress` owner.
- [ ] 1.3 Verify the released module skill descriptor and core module discovery/safe-write contracts against current repository reality.

## 2. Specification and failing-first evidence

- [ ] 2.1 Finalize descriptor, discovery, trust, canonical `.agents/skills`, inventory, collision, update, and uninstall deltas without adding workflow content or adapters.
- [ ] 2.2 Before any Section 3 implementation, add success and failure tests
  mapped in `requirements-evidence.yaml` to every discovery, export,
  idempotency, drift, collision, uninstall, trust, integrity, compatibility,
  digest-mismatch, and unchanged signed-module pass-through scenario.
- [ ] 2.3 After the scenario mapping is complete, run the targeted tests before
  production edits and record failing-first results in a newly created
  `TDD_EVIDENCE.md`.

## 3. Minimal distribution implementation

- [ ] 3.1 Implement module-owned skill discovery and integrity/compatibility validation.
- [ ] 3.2 Implement canonical `.agents/skills` installation/export and inventory-backed update/uninstall.
- [ ] 3.3 Verify `specfact-preflight` and the implementation-check workflow pass through from the signed module unchanged; do not add validator, checkpoint, or workflow semantics to core.

## 4. Passing evidence and quality gates

- [ ] 4.1 Re-run mapped tests and capture passing evidence after implementation.
- [ ] 4.2 Run required format, type, lint, contract, smart-test, test, and SpecFact code-review gates; resolve all findings.
- [ ] 4.3 Run `openspec status --change ai-integration-01-agent-skill --json` and `openspec validate ai-integration-01-agent-skill --strict`.
- [ ] 4.4 Document canonical export, conflicts, uninstall, and ownership limits using observed behavior.

## 5. Delivery and post-merge cleanup

- [ ] 5.1 Hand the exact installation/export contract to #253 and keep external adapter packaging downstream.
- [ ] 5.2 Open the implementation PR to `dev` as the final pre-merge task, linking #251 and the signed module dependency.
- [ ] 5.3 After merge, run `openspec archive ai-integration-01-agent-skill`, update ordering/wiki source state, and remove the dedicated worktree and merged branch.
