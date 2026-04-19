# Tasks: security-01-unified-findings-model

## 1. Branch and dependency guardrails

- [ ] 1.1 Create worktree branch `feature/security-01-unified-findings-model` from `dev`.
- [ ] 1.2 Confirm `policy-engine` and `policy-02-packs-and-modes` are the authority; reuse, do not redefine.
- [ ] 1.3 Coordinate with three module-side companion changes (SAST/SCA/secret, license, PII/GDPR).

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
- [ ] 4.4 Full quality gate.

## 5. Delivery

- [ ] 5.1 Mirror to wiki; rebuild graph.
- [ ] 5.2 Update `openspec/CHANGE_ORDER.md`; coordinate three module companions.
- [ ] 5.3 Open PR to `dev`.
