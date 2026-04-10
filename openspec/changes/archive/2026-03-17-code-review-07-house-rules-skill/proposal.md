# Change: house_rules Skill (ai-integration-01 Compliant) and Auto-Updater

## Why

The review findings and ledger data are only useful if they influence future coding sessions. The `house_rules.md` skill converts accumulated violation patterns into a compact, self-updating context file (≤35 lines) injected into every Claude Code session and every n8n F-2 container. Without this feedback loop, each session starts cold with no awareness of which patterns the codebase consistently violates.

This change follows the `ai-integration-01` open Agent Skills standard — skill file at `skills/specfact-code-review/SKILL.md` in specfact-cli, installable via `specfact ide skill install --type code-review`.

**ALIGNMENT NOTES (from overlap analysis):**

- Skill file lives at `skills/specfact-code-review/SKILL.md` (not `.claude/skills/`) — follows ai-integration-01 standard
- Does NOT modify `CLAUDE.md` directly — that is owned by `ai-integration-03`
- house_rules content is the dynamic body; delivery mechanism follows ai-integration-01

## What Changes

- **NEW**: `rules/updater.py` — reads ledger findings (last 20 runs), counts violation frequency, surfaces rules with >=3 hits, prunes rules with 0 hits for 10+ consecutive runs, enforces ≤35 line cap, increments version header
- **NEW**: `specfact code review rules show` — prints current house_rules skill content
- **NEW**: `specfact code review rules update` — re-derives house_rules from ledger + recent findings
- **NEW**: `specfact code review rules init` — creates default `SKILL.md` for new projects
- **NEW**: `skills/specfact-code-review/SKILL.md` (in specfact-cli repo) — ai-integration-01 compliant YAML frontmatter + Markdown body (DO/DON'T rules + TOP VIOLATIONS section)
- **NEW**: `.cursor/rules/house_rules.mdc` mirror (auto-maintained)
- **CONSTRAINT**: Skill file never exceeds 35 lines (hard cap with assertion)
- **CONSTRAINT**: No direct `CLAUDE.md` modifications (ai-integration-03 owns that path)
- **NEW**: Unit tests for `updater.py` (TDD-first)

## Capabilities

### New Capabilities

- `house-rules-skill`: ai-integration-01 compliant skill file with auto-updating DO/DON'T rules derived from ledger
- `rules-commands`: `specfact code review rules show|update|init` subcommands
- `house-rules-updater`: Algorithm to surface frequent violations and prune resolved rules

### Modified Capabilities

- `specfact-ide-skill-install` (ai-integration-01): extended with `--type code-review` selector (soft dependency)

---

## Impact

- Depends on `code-review-01-module-scaffold`, `code-review-06-reward-ledger`
- Soft dependency on `ai-integration-01` for `specfact ide skill install --type code-review`; skill file is usable standalone before ai-integration-01 ships
- **Documentation**: Add rules commands and house_rules skill usage to `docs/modules/code-review.md`

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: TBD
- **Issue URL**: TBD
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
