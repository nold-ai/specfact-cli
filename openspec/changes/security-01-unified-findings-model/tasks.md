# Tasks: security-01-unified-findings-model

## 1. Branch and dependency guardrails

- [ ] 1.1 Create worktree branch `feature/security-01-unified-findings-model` from `origin/dev` (per `AGENTS.md`).
- [ ] 1.2 Run `hatch env create` in the worktree to provision the environment.
- [ ] 1.3 Pre-flight checks: dependencies resolve, `hatch run smart-test-status`, `hatch run contract-test-status`, lint
  smoke as applicable, and no missing local credentials for integration tests — complete before deeper implementation
  tasks.
- [ ] 1.4 Confirm `policy-engine` and `policy-02-packs-and-modes` are the authority; reuse, do not redefine.
- [ ] 1.5 Coordinate with three module-side companion changes (SAST/SCA/secret, license, PII/GDPR).

## 2. Spec-first and test-first preparation

- [ ] 2.1 Finalize `specs/security-findings/spec.md`.
- [ ] 2.2 Write pydantic tests for `SecurityFinding` (per-category required fields, enum, fingerprint determinism).
- [ ] 2.3 Write CVSS→severity mapping tests (band boundaries, up-rate rejection).
- [ ] 2.4 Write policy-pack tests (deny-list SPDX, advisory vs hard exit codes).
- [ ] 2.5 Write CLI tests (category filter, envelope integration).
- [ ] 2.6 Capture failing-first in `TDD_EVIDENCE.md`.

## 3. Implementation

- [ ] 3.1 Implement `SecurityFinding` in `src/specfact_cli/reviews/security/models.py`.
- [ ] 3.2 Implement CVSS mapping table + scorer in `src/specfact_cli/reviews/security/scorer.py`.
- [ ] 3.3 Extend `policy-engine` packs loader to accept `security/` namespace.
- [ ] 3.4 Implement `specfact review security` command in `src/specfact_cli/commands/review_security.py`.
- [ ] 3.5 Extend `ReviewReport` envelope to carry `security` section.
- [ ] 3.6 Wire optional evidence emission (knowledge-01 schema).

## 4. Validation and documentation

- [ ] 4.1 Re-run tests; update `TDD_EVIDENCE.md`.
- [ ] 4.2 Document security model + policy-pack schema in `docs/agent-rules/`.
- [ ] 4.3 Run `openspec validate security-01-unified-findings-model --strict`.
- [ ] 4.4 **Full quality gate** (run in order; record results in `TDD_EVIDENCE.md`):
  - [ ] 4.4.1 `hatch run format`
  - [ ] 4.4.2 `hatch run type-check`
  - [ ] 4.4.3 `hatch run lint` (when touched paths are lint-gated)
  - [ ] 4.4.4 `hatch run contract-test`
  - [ ] 4.4.5 `hatch run smart-test` (or `hatch test --cover -v` when the smart runner requests a full run)
  - [ ] 4.4.6 `hatch run specfact code review run --json --out .specfact/code-review.json` (refresh review gate output)

## 5. Delivery

- [ ] 5.1 Mirror to wiki; rebuild graph.
- [ ] 5.2 Update `openspec/CHANGE_ORDER.md`; coordinate three module companions.
- [ ] 5.3 Open PR to `dev`.
- [ ] 5.4 After merge, perform repository worktree cleanup (`git worktree remove`, `git branch -d`, `git worktree prune`
  per `AGENTS.md`) and clear stray untracked artifacts from local validation runs.
- [ ] 5.5 From repository root after merge, run `openspec archive security-01-unified-findings-model` (exact change-id; do
  not manually move `openspec/changes/` folders).
