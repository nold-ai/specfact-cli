# Tasks: review-resiliency-01-contracts

## 1. Branch and dependency guardrails

- [ ] 1.1 Create worktree branch `feature/review-resiliency-01-contracts` from `dev`.
- [ ] 1.2 Confirm `review-finding-model`, `review-report-model`, `review-scorer`, `review-cli-contracts` are the authority for shared patterns — reuse, do not redefine.
- [ ] 1.3 Coordinate with modules repo owner for companion `review-resiliency-01-module` (bundle).

## 2. Spec-first and test-first preparation

- [ ] 2.1 Finalize `specs/review-resiliency/spec.md`.
- [ ] 2.2 Write pydantic tests for `ResiliencyFinding` (enum, rule-id pattern).
- [ ] 2.3 Write scorer tests: severity fixed per rule-id, profile override rules.
- [ ] 2.4 Write CLI tests: exit-code × enforcement mode matrix, JSON schema, envelope integration.
- [ ] 2.5 Capture failing-first in `TDD_EVIDENCE.md`.

## 3. Implementation

- [ ] 3.1 Implement `ResiliencyFinding` in `src/specfact_cli/reviews/resiliency/models.py`.
- [ ] 3.2 Implement rule table in `src/specfact_cli/reviews/resiliency/rules.py`.
- [ ] 3.3 Implement `ResiliencyScorer` in `src/specfact_cli/reviews/resiliency/scorer.py`.
- [ ] 3.4 Implement `specfact review resiliency` command in `src/specfact_cli/commands/review_resiliency.py`.
- [ ] 3.5 Extend `ReviewReport` envelope to carry `resiliency` section.
- [ ] 3.6 Wire optional evidence emission (knowledge-01 schema) behind soft dependency.

## 4. Validation and documentation

- [ ] 4.1 Re-run tests; update `TDD_EVIDENCE.md`.
- [ ] 4.2 Document reviewer surface in `docs/` alongside code-review.
- [ ] 4.3 Run `openspec validate review-resiliency-01-contracts --strict`.
- [ ] 4.4 Full quality gate.

## 5. Delivery

- [ ] 5.1 Mirror to wiki; rebuild graph.
- [ ] 5.2 Update `openspec/CHANGE_ORDER.md` and coordinate companion module change.
- [ ] 5.3 Open PR to `dev`.
