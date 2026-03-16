# Tasks: Reward Ledger Supabase Persistence

## TDD / SDD order (enforced)

Tests before code. Do not implement until failing tests exist.

---

## 1. Create git worktrees

- [x] 1.1 `git fetch origin` in both `specfact-cli` and `specfact-cli-modules`
- [x] 1.2 Create `feature/code-review-06-reward-ledger` worktree in `../specfact-cli-worktrees/feature/code-review-06-reward-ledger` for OpenSpec artifacts
- [x] 1.3 Create `feature/code-review-06-reward-ledger` worktree in `../specfact-cli-modules-worktrees/feature/code-review-06-reward-ledger` for module implementation
- [x] 1.4 Bootstrap both worktrees (`hatch env create`; `hatch run dev-deps` in modules repo; pre-flight status commands in `specfact-cli`)

## 2. Verify blocker resolved

- [x] 2.1 Confirm `code-review-01-module-scaffold` is merged (ReviewReport model required)

## 3. Write DDL migration

- [x] 3.1 Create bundle-local DDL at `packages/specfact-code-review/src/specfact_code_review/resources/supabase/review_ledger_ddl.sql` with `ai_sync.review_runs` and `ai_sync.reward_ledger` tables
- [x] 3.2 Verify DDL does not conflict with existing `coding_run_logs` / `active_runs` tables (inspect current ai_sync schema)

## 4. Write tests BEFORE implementation (TDD-first)

- [x] 4.1 Write `tests/unit/specfact_code_review/ledger/test_client.py`
  - [x] 4.1.1 Test `record_run` with Supabase available (mock HTTP calls) → inserts row
  - [x] 4.1.2 Test `record_run` without SUPABASE_URL → writes to local JSON
  - [x] 4.1.3 Test streak pass bonus at streak >= 5
  - [x] 4.1.4 Test streak block penalty at streak >= 3
  - [x] 4.1.5 Test `get_status` returns correct dict
  - [x] 4.1.6 Test coin delta formula: `reward_delta / 10.0`
- [x] 4.2 Write `tests/unit/specfact_code_review/ledger/test_commands.py`
  - [x] 4.2.1 Test `ledger update` reads valid JSON stdin → calls record_run
  - [x] 4.2.2 Test `ledger update` with invalid JSON → exit 1, stderr message
  - [x] 4.2.3 Test `ledger status` prints coins (2dp), streak, verdict
  - [x] 4.2.4 Test `ledger reset` without --confirm → error, no deletion
  - [x] 4.2.5 Test `ledger reset --confirm` → local ledger cleared, exit 0
- [x] 4.3 Run tests → expect failure; record in `TDD_EVIDENCE.md`

## 5. Implement ledger

- [x] 5.1 Implement `ledger/client.py` — `LedgerClient` with Supabase + local JSON fallback; all public methods with `@require`/`@ensure`/`@beartype`
- [x] 5.2 Implement `ledger/commands.py` — `update`, `status`, `reset` Typer commands
- [x] 5.3 Create `ledger/__init__.py`

## 6. Quality gates

- [x] 6.1 Run tests → expect passing; record in `TDD_EVIDENCE.md`
- [x] 6.2 `hatch run format && hatch run type-check && hatch run contract-test && hatch run lint`
- [x] 6.3 Test local JSON fallback manually from the modules worktree using the local bundle source:
  `HOME=/tmp/specfact-ledger-smoke PYTHONPATH=packages/specfact-code-review/src SPECFACT_MODULES_ROOTS=packages SUPABASE_URL="" .venv/bin/specfact code review ledger status`

## 7. Module signing, docs, version, changelog

- [x] 7.1 Verify/re-sign module
- [x] 7.2 Update `docs/modules/code-review.md` with ledger commands section; document offline fallback
- [x] 7.3 Bump minor version (new feature); update CHANGELOG.md

## 8. Create GitHub issue and PR

- [x] 8.1 Link existing issue: `[Change] code-review-06 - Reward Ledger Supabase Persistence and ledger Subcommands` (#395)
- [ ] 8.2 Update proposal.md Source Tracking; commit, push, create PR

## Post-merge cleanup

- [ ] Remove worktree, delete branch, prune
