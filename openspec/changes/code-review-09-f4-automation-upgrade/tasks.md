# Tasks: Upgrade F-4 to Use specfact code review run

## TDD / SDD order (enforced)

Tests before code. Do not implement until failing tests exist.
Note: n8n workflow changes cannot be unit-tested in the same way; integration tests use n8n test mode.

---

## 1. Create git worktree

- [ ] 1.1 `git fetch origin`
- [ ] 1.2 `git worktree add ../specfact-cli-worktrees/feature/code-review-09-f4-automation-upgrade -b feature/code-review-09-f4-automation-upgrade origin/dev`
- [ ] 1.3 `cd ../specfact-cli-worktrees/feature/code-review-09-f4-automation-upgrade`
- [ ] 1.4 `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`

## 2. Verify blockers resolved

- [ ] 2.1 Confirm `code-review-01-module-scaffold` merged (ReviewReport schema)
- [ ] 2.2 Confirm `code-review-02-ruff-radon-runners` merged
- [ ] 2.3 Confirm `code-review-03-type-governance-runners` merged
- [ ] 2.4 Confirm `code-review-04-contract-test-runners` merged
- [ ] 2.5 Confirm `code-review-06-reward-ledger` merged (ledger update command)
- [ ] 2.6 Resolve open questions (see design.md):
  - [ ] 2.6.1 Confirm crosshair in `specfact-coding-worker` Docker image
  - [ ] 2.6.2 Confirm Supabase service role key covers new tables
  - [ ] 2.6.3 Define max concurrent review processes per VPS run

## 3. Write tests / validation scripts BEFORE implementation (TDD-first)

- [ ] 3.1 Write n8n workflow validation script: `scripts/validate_f4_workflow.py`
  - [ ] 3.1.1 Validate F-4 workflow JSON contains "specfact code review run" node (not "codex review")
  - [ ] 3.1.2 Validate F-4 has three output branches: PASS, WARN, BLOCK
  - [ ] 3.1.3 Validate "Update Reward Ledger" node exists and pipes to `ledger update`
- [ ] 3.2 Write container script unit tests: `tests/unit/test_container_pre_commit_gate.py`
  - [ ] 3.2.1 Test exit code 0 → commit proceeds
  - [ ] 3.2.2 Test exit code 1 → commit blocked, REVIEW_BLOCKED callback fired
  - [ ] 3.2.3 Test HOUSE_RULES env var is set from skill content
  - [ ] 3.2.4 Test specfact unavailable → graceful degradation (warning, commit proceeds)
- [ ] 3.3 Run tests → expect failure; record in `TDD_EVIDENCE.md`

## 4. Implement n8n F-4 workflow changes

- [ ] 4.1 Export current F-4 workflow JSON from n8n
- [ ] 4.2 Replace "Run Codex Review" node with "Run specfact code review run --json"
- [ ] 4.3 Replace parse logic with ReviewReport JSON parser (SP-001 models)
- [ ] 4.4 Wire `overall_verdict` to three-branch routing (PASS/WARN/BLOCK)
- [ ] 4.5 Add "Update Reward Ledger" node after review run (all branches)
- [ ] 4.6 Replace "Run Codex Auto-Fix" with "Run specfact code review run --fix"
- [ ] 4.7 Import updated workflow JSON to n8n
- [ ] 4.8 Test in n8n using `n8n test workflow` mode

## 5. Implement F-2 house_rules injection

- [ ] 5.1 Modify F-2 container launch to read `SKILL.md` and set `HOUSE_RULES` env var (truncated to 2000 chars)
- [ ] 5.2 Verify `HOUSE_RULES` is accessible inside container

## 6. Implement stage 6 pre-commit gate in coding-workflow.js

- [ ] 6.1 Add stage 6 logic: run `specfact code review run --score-only` on changed files
- [ ] 6.2 Exit code 1 → do not commit, fire `REVIEW_BLOCKED` callback with score/file context
- [ ] 6.3 Exit code 0 → proceed with git commit
- [ ] 6.4 Add stage 5 `context.house_rules` to stdin JSON

## 7. Quality gates and integration validation

- [ ] 7.1 Run tests → expect passing; record in `TDD_EVIDENCE.md`
- [ ] 7.2 `hatch run format && hatch run type-check && hatch run lint`
- [ ] 7.3 Run full automation workflow in staging environment: verify PASS/WARN/BLOCK routing, ledger update, BLOCK prevents commit
- [ ] 7.4 Verify `HOUSE_RULES` visible to coding CLI in container (print context.house_rules in dry-run)

## 8. Documentation

- [ ] 8.1 Update `docs/modules/code-review.md` with CI/automation integration section
- [ ] 8.2 Update internal runbook with F-4 upgrade notes and open questions resolution

## 9. Version and changelog

- [ ] 9.1 Bump minor version; update CHANGELOG.md: `Changed: F-4 code review upgraded to specfact code review run with reward ledger and pre-commit gate`

## 10. Create GitHub issue and PR

- [ ] 10.1 Create issue: `[Change] Upgrade F-4 code review to use specfact code review run`
- [ ] 10.2 Update proposal.md Source Tracking; commit, push, create PR

## Post-merge cleanup

- [ ] Remove worktree, delete branch, prune
