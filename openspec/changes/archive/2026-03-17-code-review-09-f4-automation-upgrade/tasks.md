# Tasks: Integrate specfact code review into pre-commit workflows

## TDD / SDD order (enforced)

Tests before code. Do not implement until failing tests exist.

---

## 1. Create git worktree

- [x] 1.1 `git fetch origin`
- [x] 1.2 `git worktree add ../specfact-cli-worktrees/feature/code-review-09-f4-automation-upgrade -b feature/code-review-09-f4-automation-upgrade origin/dev`
- [x] 1.3 `cd ../specfact-cli-worktrees/feature/code-review-09-f4-automation-upgrade`
- [x] 1.4 `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`

## 2. Verify blockers resolved

- [x] 2.1 Confirm `code-review-01-module-scaffold` merged (ReviewReport schema)
- [x] 2.2 Confirm `code-review-02-ruff-radon-runners` merged
- [x] 2.3 Confirm `code-review-03-type-governance-runners` merged
- [x] 2.4 Confirm `code-review-04-contract-test-runners` merged
- [x] 2.5 Confirm `code-review-06-reward-ledger` merged (ledger update command)
- [x] 2.6 Confirm the integration surface is repo-owned: `.pre-commit-config.yaml`, docs, and any supporting scripts

## 3. Write tests / validation scripts BEFORE implementation (TDD-first)

- [x] 3.1 Add failing tests or validation coverage for the repository pre-commit review gate
  - [x] 3.1.1 Validate PASS and PASS_WITH_ADVISORY verdicts allow commit flow to continue
  - [x] 3.1.2 Validate FAIL verdict blocks commit flow
  - [x] 3.1.3 Validate only relevant staged source files are passed to the review command
  - [x] 3.1.4 Validate missing-tool setup errors are actionable
- [x] 3.2 Add failing documentation checks or snapshots for portable project adoption guidance if applicable
- [x] 3.3 Run targeted validation -> expect failure; record in `TDD_EVIDENCE.md`

## 4. Implement repository pre-commit integration

- [x] 4.1 Update `.pre-commit-config.yaml` to run `specfact code review run` before commit success
- [x] 4.2 Add any repo-owned helper script needed for staged-file filtering, rules-path defaults, or actionable setup errors
- [x] 4.3 Ensure the hook blocks only on blocking review verdicts
- [x] 4.4 Ensure the hook remains usable for local development speed and does not review unrelated files

## 5. Document portable adoption and ledger posture

- [x] 5.1 Update `docs/modules/code-review.md` with this repo's pre-commit integration
- [x] 5.2 Add copyable instructions for adding the same review gate to any project later
- [x] 5.3 Document optional `house_rules` workflow usage for projects that want project-specific review guidance
- [x] 5.4 Document that local JSON ledger storage is the normal local/offline path, with Supabase or another backend remaining optional when configured

## 6. Quality gates and integration validation

- [x] 6.1 Run targeted tests/validation -> expect passing; record in `TDD_EVIDENCE.md`
- [x] 6.2 Run `pre-commit run --all-files` or an equivalent targeted pre-commit validation pass
- [x] 6.3 `hatch run format`
- [x] 6.4 `hatch run type-check`
- [x] 6.5 `hatch run lint`

## 7. Version and changelog

- [x] 7.1 Bump minor version; update `CHANGELOG.md` for pre-commit review integration and portable adoption guidance

## 8. GitHub issue and PR

- [x] 8.1 Update issue #393 to match the rewritten change scope
- [x] 8.2 Update proposal.md Source Tracking if needed; commit, push, create PR

## Post-merge cleanup

- [x] Remove worktree, delete branch, prune
