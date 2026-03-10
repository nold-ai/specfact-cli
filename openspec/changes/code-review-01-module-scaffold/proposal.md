# Change: specfact-code-review Module Scaffold with Pydantic Models

## Why

The current coding automation pipeline runs a generic `codex review` pass but has no structured scoring, no persistent quality ledger, and no contract-bound enforcement gates. A dedicated `nold-ai/specfact-code-review` installable module closes these gaps by providing a governed entry point for all code-review subcommands under `specfact code review`.

This change establishes the foundation: the module package scaffold, the governance-01-compatible evidence envelope (`ReviewReport`), the `ReviewFinding` Pydantic model, and the scoring algorithm — everything SP-002 through SP-009 depend on.

## What Changes

- **NEW**: `packages/specfact-code-review/` module package in `specfact-cli-modules`
- **NEW**: `module-package.yaml` with `bundle_group_command: code`, tier `official`, `core_compatibility: >=0.40.0,<1.0.0`
- **NEW**: `ReviewFinding` Pydantic model — fields: `category`, `severity`, `tool`, `rule`, `file`, `line`, `message`, `fixable`
- **NEW**: `ReviewReport` governance-01-compatible evidence envelope — standard fields: `schema_version`, `run_id`, `timestamp`, `overall_verdict` (`PASS`/`PASS_WITH_ADVISORY`/`FAIL`), `ci_exit_code` (0/1); review-specific extensions: `score`, `reward_delta`, `findings[]`, `summary`, `house_rules_updates`
- **NEW**: `scorer.py` — base_score=100, per-violation deductions, bonus conditions, `reward_delta = score - 80`
- **NEW**: Typer app wired to extend `specfact code` with a `review` subgroup via `bundle_group_command: code`
- **NEW**: `specfact code review --help` surfaces the review subgroup after module install
- **NEW**: Unit tests for `ReviewFinding`, `ReviewReport`, and `scorer.py` (TDD-first)

Violation categories: `clean_code`, `security`, `type_safety`, `contracts`, `testing`, `style`, `architecture`.

Scoring algorithm:
```
base_score = 100
Deductions: error/blocking=-15, error/fixable=-5, warning=-2, info=-1
Bonuses: +5 each for: zero LOC > 120, zero complexity > 12, all APIs with icontract, coverage >= 90%, no suppressions
reward_delta = score - 80  (range: -80..+20)
```

## Capabilities

### New Capabilities

- `code-review-module`: Installable `nold-ai/specfact-code-review` module extending `specfact code` with a `review` subgroup
- `review-finding-model`: Pydantic `ReviewFinding` model for structured code-review violation representation
- `review-report-model`: governance-01-compatible `ReviewReport` evidence envelope with scoring extensions
- `review-scorer`: Scoring algorithm converting findings + bonuses into `score` and `reward_delta`

### Modified Capabilities

- `specfact-code` command group: extended with `review` subgroup (additive; no existing commands modified)

---

## Impact

- **New module** in `specfact-cli-modules` — no breaking changes to existing `specfact-cli` commands
- **governance-01 alignment**: `ReviewReport` extends the governance-01 evidence envelope (standard fields present from day 1); does not hard-block on governance-01 shipping first
- **Additive only** — `bundle_group_command: code` merges into the existing `code` group via `_merge_typer_apps`
- **Documentation**: Add `docs/modules/code-review.md` page covering install, commands, scoring algorithm, JSON output schema; update `docs/index.md` and sidebar navigation

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: TBD
- **Issue URL**: TBD
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
