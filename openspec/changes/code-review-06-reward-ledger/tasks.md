# Tasks: Reward Ledger Supabase Persistence

## TDD / SDD order (enforced)

Tests before code. Do not implement until failing tests exist.

---

## 1. Create git worktree

- [ ] 1.1 `git fetch origin`
- [ ] 1.2 `git worktree add ../specfact-cli-worktrees/feature/code-review-06-reward-ledger -b feature/code-review-06-reward-ledger origin/dev`
- [ ] 1.3 `cd ../specfact-cli-worktrees/feature/code-review-06-reward-ledger`
- [ ] 1.4 `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`

## 2. Verify blocker resolved

- [ ] 2.1 Confirm `code-review-01-module-scaffold` is merged (ReviewReport model required)

## 3. Write DDL migration

- [ ] 3.1 Create `infra/supabase/review_ledger_ddl.sql` with `ai_sync.review_runs` and `ai_sync.reward_ledger` tables
- [ ] 3.2 Verify DDL does not conflict with existing `coding_run_logs` / `active_runs` tables (inspect current ai_sync schema)

## 4. Write tests BEFORE implementation (TDD-first)

- [ ] 4.1 Write `tests/unit/specfact_code_review/ledger/test_client.py`
  - [ ] 4.1.1 Test `record_run` with Supabase available (mock HTTP calls) → inserts row
  - [ ] 4.1.2 Test `record_run` without SUPABASE_URL → writes to local JSON
  - [ ] 4.1.3 Test streak pass bonus at streak >= 5
  - [ ] 4.1.4 Test streak block penalty at streak >= 3
  - [ ] 4.1.5 Test `get_status` returns correct dict
  - [ ] 4.1.6 Test coin delta formula: `reward_delta / 10.0`
- [ ] 4.2 Write `tests/unit/specfact_code_review/ledger/test_commands.py`
  - [ ] 4.2.1 Test `ledger update` reads valid JSON stdin → calls record_run
  - [ ] 4.2.2 Test `ledger update` with invalid JSON → exit 1, stderr message
  - [ ] 4.2.3 Test `ledger status` prints coins (2dp), streak, verdict
  - [ ] 4.2.4 Test `ledger reset` without --confirm → error, no deletion
  - [ ] 4.2.5 Test `ledger reset --confirm` → local ledger cleared, exit 0
- [ ] 4.3 Run tests → expect failure; record in `TDD_EVIDENCE.md`

## 5. Implement ledger

- [ ] 5.1 Implement `ledger/client.py` — `LedgerClient` with Supabase + local JSON fallback; all public methods with `@require`/`@ensure`/`@beartype`
- [ ] 5.2 Implement `ledger/commands.py` — `update`, `status`, `reset` Typer commands
- [ ] 5.3 Create `ledger/__init__.py`

## 6. Quality gates

- [ ] 6.1 Run tests → expect passing; record in `TDD_EVIDENCE.md`
- [ ] 6.2 `hatch run format && hatch run type-check && hatch run contract-test && hatch run lint`
- [ ] 6.3 Test local JSON fallback manually: `SUPABASE_URL="" specfact code review ledger status`

## 7. Module signing, docs, version, changelog

- [ ] 7.1 Verify/re-sign module
- [ ] 7.2 Update `docs/modules/code-review.md` with ledger commands section; document offline fallback
- [ ] 7.3 Bump minor version (new feature); update CHANGELOG.md

## 8. Create GitHub issue and PR

- [ ] 8.1 Create issue: `[Change] Add reward ledger Supabase persistence and ledger subcommands`
- [ ] 8.2 Update proposal.md Source Tracking; commit, push, create PR

## Post-merge cleanup

- [ ] Remove worktree, delete branch, prune
