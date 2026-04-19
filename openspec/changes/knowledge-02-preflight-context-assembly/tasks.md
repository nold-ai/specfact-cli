# Tasks: knowledge-02-preflight-context-assembly

## 1. Branch and dependency guardrails

- [ ] 1.1 Create worktree branch `feature/knowledge-02-preflight-context-assembly` from `dev`.
- [ ] 1.2 Confirm knowledge-01 (schema + backend) is merged.
- [ ] 1.3 Reconfirm scope against plan and proposal.

## 2. Spec-first and test-first preparation

- [ ] 2.0 Documentation research: review `openspec/config.yaml` and `/opsx:ff` scaffolding rules; identify user-facing doc updates and `.openspec.yaml` population tests needed (link notes to 4.2 and to `TDD_EVIDENCE.md`).
- [ ] 2.1 Finalize `specs/preflight-context-assembly/spec.md`.
- [ ] 2.2 Write assembler tests: tag matching, budget packer, deterministic ordering.
- [ ] 2.3 Write authoring-gate tests: `.openspec.yaml` population, disabled-reason enforcement.
- [ ] 2.4 Write validation-gate tests: blocker + advisory enforcement paths.
- [ ] 2.5 Write inspection-command tests (`--json`, non-mutating).
- [ ] 2.6 Capture failing-first in `TDD_EVIDENCE.md`.

## 3. Implementation

- [ ] 3.1 Implement tag extractor in `src/specfact_cli/memory/preflight/extractor.py`.
- [ ] 3.2 Implement rule matcher + priority sorter + budget packer in `src/specfact_cli/memory/preflight/assembler.py`.
- [ ] 3.3 Extend `.openspec.yaml` schema to include `preflight_rules`, `preflight_rules_snapshot_sha`, `preflight_disabled_reason`.
- [ ] 3.4 Wire authoring gate into `openspec new change` and `opsx:ff` entry points.
- [ ] 3.5 Implement validation gate integrated with `code-review-module` finding model.
- [ ] 3.6 Implement `specfact memory preflight` inspection command.

## 4. Validation and documentation

- [ ] 4.1 Re-run tests; update `TDD_EVIDENCE.md`.
- [ ] 4.2 Document preflight workflow + `.openspec.yaml` extension in agent-rules.
- [ ] 4.3 Dogfood: author a new change for this repo, verify `preflight_rules` populates correctly.
- [ ] 4.4 Run `openspec validate knowledge-02-preflight-context-assembly --strict`.
- [ ] 4.5 **Full quality gate** (run in order; update `TDD_EVIDENCE.md` after tests):
  - [ ] 4.5.1 `hatch run format`
  - [ ] 4.5.2 `hatch run type-check`
  - [ ] 4.5.3 `hatch run contract-test`
  - [ ] 4.5.4 `hatch run smart-test` (or `hatch run smart-test-full` if the smart runner requests it)
  - [ ] 4.5.5 `hatch run lint` if touched scope includes linted paths
  - [ ] 4.5.6 `openspec validate knowledge-02-preflight-context-assembly --strict` (repeat after doc-only edits)
  - [ ] 4.5.7 Re-run tests that cover `.openspec.yaml` / `preflight_rules` population and inspection JSON schema

## 5. Delivery

- [ ] 5.1 Mirror to wiki; rebuild graph.
- [ ] 5.2 Update `openspec/CHANGE_ORDER.md`.
- [ ] 5.3 Open PR to `dev`.
- [ ] 5.4 After merge, from the **same repository worktree** used for this change, run cleanup: `git worktree remove <worktree-path>`, `git branch -d feature/knowledge-02-preflight-context-assembly`, `git worktree prune` (and `git remote prune origin` if stale remotes accumulate) per `AGENTS.md`.
