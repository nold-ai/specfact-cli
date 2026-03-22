# Tasks: clean-code-01-principle-gates

## 1. Branch and dependency guardrails

- [ ] 1.1 Create dedicated worktree branch `feature/clean-code-01-principle-gates` from `dev` before implementation work: `scripts/worktree.sh create feature/clean-code-01-principle-gates`.
- [ ] 1.2 Confirm `code-review-zero-findings` has recorded a zero-finding self-review baseline and that the modules repo change `clean-code-02-expanded-review-module` is available for consumption.
- [ ] 1.3 Reconfirm scope against the 2026-03-22 clean-code implementation plan and the updated `openspec/CHANGE_ORDER.md`.

## 2. Spec-first and test-first preparation

- [ ] 2.1 Finalize `specs/` deltas for clean-code charter references, clean-code compliance gating, and staged LOC/nesting checks.
- [ ] 2.2 Add or update tests derived from the new scenarios before touching production code.
- [ ] 2.3 Run targeted tests and capture failing-first evidence in `TDD_EVIDENCE.md`.

## 3. Implementation

- [ ] 3.1 Update instruction surfaces (`AGENTS.md`, `CLAUDE.md`, `.cursor/rules/clean-code-principles.mdc`, `.github/copilot-instructions.md`, relevant `.codex` skill entry points) to reference the canonical clean-code charter.
- [ ] 3.2 Wire specfact-cli review and CI flows to consume the expanded clean-code categories from the modules repo without introducing a second clean-code configuration model.
- [ ] 3.3 Adopt Phase A LOC, nesting-depth, and parameter-count checks through the review integration path and preserve the Phase B thresholds as a later change.

## 4. Validation and documentation

- [ ] 4.1 Re-run targeted tests, review flows, and quality gates until all changed scenarios pass.
- [ ] 4.2 Update contributor-facing docs that explain AI instruction files, repo review rules, and clean-code governance.
- [ ] 4.3 Run `openspec validate clean-code-01-principle-gates --strict` and resolve all issues.

## 5. Delivery

- [ ] 5.1 Update `openspec/CHANGE_ORDER.md` dependency notes if implementation sequencing changes again.
- [ ] 5.2 Open a PR from `feature/clean-code-01-principle-gates` to `dev` with spec/test/code/docs evidence.
