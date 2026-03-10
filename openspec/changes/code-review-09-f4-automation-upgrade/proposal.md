# Change: Upgrade F-4 (Code Review) to Use specfact code review run

## Why

The current F-4 node in the n8n coding automation workflow uses a generic `codex review` pass with no structured scoring, no ledger update, and no pre-commit BLOCK gate. This change replaces that with `specfact code review run --json`, wires the output to the reward ledger, injects `house_rules.md` context into F-2 container launches, and adds a pre-commit gate in stage 6 of the coding container script.

This closes the feedback loop: AI generates code → review runs automatically → ledger updates → house_rules improves → next session benefits.

## What Changes

**n8n F-2 workflow:**
- Read `house_rules.md` at container launch; inject as `HOUSE_RULES` env var

**n8n F-4 workflow:**
- Replace "Run Codex Review" node with "Run specfact code review run --json"
- Replace parse logic with `ReviewReport` schema parser (SP-001 models)
- Wire `overall_verdict` (PASS/PASS_WITH_ADVISORY/FAIL) to branch routing
- Add "Update Reward Ledger" node: pipe review JSON to `specfact code review ledger update`
- Replace "Run Codex Auto-Fix" with "Run specfact code review run --fix"

**coding-workflow.js container script:**
- Stage 5: include `HOUSE_RULES` content in coding CLI stdin JSON as `context.house_rules` field
- Stage 6 (new pre-commit gate):
  - Run `specfact code review run --score-only` on changed files
  - Exit code 1 (BLOCK): do not commit; fire callback `REVIEW_BLOCKED`
  - Exit code 0 (PASS/WARN): proceed with git commit

## Capabilities

### New Capabilities

- `f4-specfact-review`: n8n F-4 node using `specfact code review run` instead of `codex review`
- `f4-ledger-update`: Automatic reward ledger update after every F-4 execution
- `f2-house-rules-injection`: `HOUSE_RULES` env var injected into every F-2 container launch
- `container-pre-commit-gate`: Stage 6 gate in coding-workflow.js preventing BLOCK commits

### Modified Capabilities

- `coding-automation-f4`: Replaced with specfact review run; branch routing on PASS/WARN/BLOCK
- `coding-automation-f2`: Extended with house_rules context injection
- `coding-automation-container-script`: Stage 5 + stage 6 modifications

---

## Impact

- Depends on `code-review-01-module-scaffold`, `code-review-02-ruff-radon-runners`, `code-review-03-type-governance-runners`, `code-review-04-contract-test-runners`, `code-review-06-reward-ledger`
- Replaces `codex` CLI in F-4 fully (codex not run in parallel)
- BLOCK verdict stops auto-commit and triggers human notification — 100% gate, no bypass
- VPS resource note: semgrep + crosshair are CPU-heavy; max concurrent `specfact code review run` processes must be defined
- `crosshair` availability in `specfact-coding-worker` Docker image must be confirmed
- **Documentation**: Add automation upgrade notes to internal runbook; update `docs/modules/code-review.md` with CI/automation integration section

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: TBD
- **Issue URL**: TBD
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
