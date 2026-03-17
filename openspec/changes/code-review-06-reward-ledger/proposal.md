# Change: Reward Ledger Supabase Persistence and ledger Subcommands

## Why

A single review run produces a `reward_delta` but without persistence there is no accumulated quality signal, no streak awareness, and no trend-over-time visibility. The reward ledger closes this gap: every review run is persisted to Supabase (`ai_sync.review_runs`, `ai_sync.reward_ledger`), accumulating coins, streaks, and violation frequency — all queryable for the house_rules auto-updater and for developer motivation.

A local JSON fallback (`~/.specfact/ledger.json`) ensures the feature works offline or when Supabase is unavailable.

## What Changes

- **NEW**: `ai_sync.review_runs` table — stores per-run metadata: session_id, issue_number, agent, changed_files, score, reward_delta, verdict, findings_json, house_rules_ver
- **NEW**: `ai_sync.reward_ledger` table — accumulates coins, streaks, last delta/verdict per agent
- **NEW**: `LedgerClient` — Supabase HTTP primary + `~/.specfact/ledger.json` fallback; all public methods decorated with `@require`/`@ensure` + `@beartype`
- **NEW**: `specfact code review ledger update` — reads `ReviewReport` JSON from stdin (piped from `review run --json`)
- **NEW**: `specfact code review ledger status` — prints coins (2dp), streak_pass, streak_block, last verdict, top-3 violations
- **NEW**: `specfact code review ledger reset` — resets local ledger (requires `--confirm`)
- **NEW**: Coin update formula: `coins += reward_delta / 10.0`; streak bonuses: pass>=5 → +0.5, block>=3 → -1.0
- **NEW**: Bundle-local Supabase DDL file: `packages/specfact-code-review/src/specfact_code_review/resources/supabase/review_ledger_ddl.sql`
- **NEW**: Unit tests for `LedgerClient` and ledger commands (TDD-first)

## Capabilities

### New Capabilities

- `reward-ledger`: Supabase-persisted reward ledger with offline JSON fallback, coin accumulation, and streak tracking
- `ledger-commands`: `specfact code review ledger update|status|reset` subcommands

---

## Impact

- Depends on `code-review-01-module-scaffold` (`ReviewReport` model)
- Requires Supabase `ai_sync` schema access (service role key); degrades gracefully without it
- DDL must not conflict with existing `coding_run_logs` / `active_runs` tables
- `specfact code review run --json | specfact code review ledger update` is the canonical pipe
- **Documentation**: Add ledger commands to `docs/modules/code-review.md`; document offline fallback

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #395
- **Issue URL**: https://github.com/nold-ai/specfact-cli/issues/395
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: in-progress
