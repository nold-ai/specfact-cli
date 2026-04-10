# Change Validation Report: ai-integration-04-intent-skills

**Validation Date**: 2026-03-05
**Change Proposal**: [proposal.md](./proposal.md)
**Validation Method**: Dry-run simulation in temporary workspace `/tmp/specfact-validation-ai-integration-04-<timestamp>`
**Source Plan**: `specfact-cli-internal/docs/internal/implementation/2026-03-05-CLAUDE-RESEARCH-INTENT-DRIVEN-DEVELOPMENT.md`

## Executive Summary

- Breaking Changes: 0 detected
- Dependent Files: 0 affected (all interfaces are new — ai-integration-01 not yet implemented)
- Impact Level: Low (new files and backwards-compatible CLI extension)
- Validation Result: **Pass**
- User Decision: N/A

## Breaking Changes Detected

None. `specfact ide skill install` and the `skills/` directory do not yet exist in the codebase — they are being created by `ai-integration-01-agent-skill` (#251, pending). The `--type` option is a new optional parameter with a backwards-compatible default (`"spec"`), posing no breaking risk on any existing callers.

## Dependencies Affected

### Critical (hard blockers — must land before implementation)

| Dependency | Issue | Status |
|---|---|---|
| `ai-integration-01-agent-skill` | [#251](https://github.com/nold-ai/specfact-cli/issues/251) | PENDING (Wave 8) |
| `requirements-01-data-model` | [#238](https://github.com/nold-ai/specfact-cli/issues/238) | PENDING (Wave 5) |
| `requirements-02-module-commands` | [#239](https://github.com/nold-ai/specfact-cli/issues/239) | PENDING (Wave 5/6) |

All three are expected — this is a Wave 8 change by design.

### Recommended Updates

None.

## Impact Assessment

- **Code Impact**: Low — 6 new Markdown skill files + 1 new `--type` CLI option (optional, backwards-compatible). No existing Python code modified.
- **Test Impact**: Low — new test files only (`test_intent_skills_install.py`, `test_intent_skills_content.py`). No existing test modifications.
- **Documentation Impact**: Medium — new guide `docs/guides/intent-capture-workflow.md`; update `docs/guides/ai-ide-workflow.md`. Sidebar navigation update required.
- **Release Impact**: Minor version bump (new feature, no breaking changes).

## Format Validation

- **proposal.md Format**: Pass
  - `# Change:` title ✓
  - `## Why`, `## What Changes`, `## Capabilities`, `## Impact` sections ✓
  - NEW/EXTEND markers in What Changes ✓
  - Capabilities linked to spec files ✓
  - Source Tracking section ✓
- **tasks.md Format**: Pass
  - Hierarchical `## 1.`, `## 2.`… structure ✓
  - Task 1 = git worktree creation ✓
  - Task 9 = PR creation (last) ✓
  - Post-merge cleanup section ✓
  - TDD / SDD order section at top ✓
  - Tests before implementation (Task 2 tests before Task 3-4 implementation) ✓
  - `TDD_EVIDENCE.md` recording tasks ✓
  - Quality gate tasks (format, type-check, lint, yaml-lint, contract-test, smart-test) ✓
  - Module signing verification task ✓
  - Version and changelog task ✓
  - GitHub issue creation task ✓
- **specs Format**: Pass
  - `####` for all scenario headers ✓
  - `## ADDED Requirements` / `## MODIFIED Requirements` delta format ✓
  - Given/When/Then with THEN/AND format ✓
  - Every requirement has ≥1 scenario ✓
- **Config.yaml Compliance**: Pass
  - Contract decorator tasks included ✓
  - Documentation research task included ✓
  - 2-hour max chunk guidance followed ✓

## OpenSpec Validation

- **Status**: Pass
- **Command**: `openspec validate ai-integration-04-intent-skills --strict`
- **Output**: `Change 'ai-integration-04-intent-skills' is valid`
- **Issues Found/Fixed**: 0

## Validation Artifacts

- Temporary workspace: `/tmp/specfact-validation-ai-integration-04-<timestamp>`
- Interface scaffolds created: none (no existing interfaces to compare against)

## Ownership Notes

- **New skill files** (`skills/specfact-intent*/SKILL.md`): owned exclusively by this change
- **`specfact ide skill install` `--type` option**: this change extends the interface defined by `ai-integration-01`; no ownership conflict (ai-integration-01 does not define `--type`)
- **`specfact ide skill list`**: delta extension; ai-integration-01 owns the base command, this change adds intent-type entries

## Wave/Sequencing Confirmation

Wave 8, blocked by:

- ai-integration-01 (#251) — skill install infrastructure
- requirements-01 (#238) + requirements-02 (#239) — skills invoke `specfact requirements capture/validate/trace`

Do not start implementation until all three blockers are archived.
