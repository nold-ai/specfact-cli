# reward-ledger Specification

## Purpose
TBD - created by archiving change code-review-06-reward-ledger. Update Purpose after archive.
## Requirements
### Requirement: Supabase Reward Ledger with Offline JSON Fallback
The system SHALL persist review run results to local `~/.specfact/ledger.json`
by default for local and offline workflows, and MAY additionally write to
Supabase `ai_sync.review_runs` plus `ai_sync.reward_ledger` when backend
configuration is present.

#### Scenario: Record run writes to local JSON by default
- **GIVEN** a `ReviewReport` with `score=85`, `reward_delta=5`, `verdict="PASS"`
- **WHEN** `LedgerClient.record_run(report)` is called in a local default setup
- **THEN** the run is appended to `~/.specfact/ledger.json` and no backend configuration is required

#### Scenario: Record run stores data in Supabase when configured
- **GIVEN** a `ReviewReport` with `score=85`, `reward_delta=5`, `verdict="PASS"` and Supabase is configured and reachable
- **WHEN** `LedgerClient.record_run(report)` is called
- **THEN** a row is inserted into `ai_sync.review_runs` and `ai_sync.reward_ledger` is updated with `coins += 0.5` and `streak_pass` incremented

#### Scenario: Record run falls back to local JSON when backend unavailable
- **GIVEN** Supabase configuration is missing or unreachable
- **WHEN** `LedgerClient.record_run(report)` is called
- **THEN** the run is appended to `~/.specfact/ledger.json` and no exception is raised

#### Scenario: Streak pass bonus applied at streak >= 5
- **GIVEN** the agent has `streak_pass=4` and a new PASS run occurs
- **WHEN** the ledger updates
- **THEN** `streak_pass` becomes `5` and an additional `+0.5` coins is added

#### Scenario: Streak block penalty applied at streak >= 3
- **GIVEN** the agent has `streak_block=2` and a new BLOCK run occurs
- **WHEN** the ledger updates
- **THEN** `streak_block` becomes `3` and `-1.0` coins is deducted

#### Scenario: Ledger status returns correct state
- **GIVEN** `cumulative_coins=12.5`, `streak_pass=3`, `last_verdict="PASS"`
- **WHEN** `LedgerClient.get_status()` is called
- **THEN** the returned dict includes `coins=12.5`, `streak_pass=3`, `last_verdict="PASS"`

