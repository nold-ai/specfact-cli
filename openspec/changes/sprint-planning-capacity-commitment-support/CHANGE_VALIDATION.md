# Change Validation Report: sprint-planning-capacity-commitment-support

**Validation Date**: 2026-01-30  
**Change Proposal**: [proposal.md](./proposal.md)  
**Validation Method**: Dry-run and format/config compliance check

## Executive Summary

- **Breaking Changes**: 0 detected
- **Dependent Files**: Additive only (new `specfact backlog sprint-summary` subcommand; existing `backlog` Typer group in `backlog_commands.py` will gain a new callback; capacity config and commitment aggregation are new modules)
- **Impact Level**: Low
- **Validation Result**: Pass
- **User Decision**: N/A (no breaking changes)
- **Command placement**: Sprint summary is under backlog command group (`specfact backlog sprint-summary`); no top-level `specfact sprint` command (per plan)

## Breaking Changes Detected

None. Change is additive: new sprint capacity config, commitment sum, sprint-summary output; existing backlog behavior unchanged.

## Dependencies Affected

- **Critical**: None
- **Recommended**: Reuse BacklogItem.sprint and BacklogItem.story_points from existing models; capacity loader pattern similar to DoR/DoD config loaders.
- **Optional**: None

## Impact Assessment

- **Code Impact**: New subcommand (sprint-summary); new or extended config loader (sprint_capacity.yaml); commitment aggregation from backlog items.
- **Test Impact**: New tests from spec scenarios (capacity config load, commitment sum, over/under output, sprint-summary CLI).
- **Documentation Impact**: agile-scrum-workflows.md, backlog-refinement.md for sprint planning.
- **Release Impact**: Patch (additive feature).

## Format Validation

- **proposal.md Format**: Pass
  - Title format: Correct (`# Change: Sprint planning (capacity and commitment) support`)
  - Required sections: All present (Why, What Changes, Capabilities, Impact)
  - "What Changes" format: Correct (bullet list with NEW/EXTEND)
  - "Capabilities" section: Present (sprint-planning)
  - "Impact" format: Correct
  - Source Tracking section: Present (GitHub Issue #170, URL, repository)
- **tasks.md Format**: Pass
  - Section headers: Hierarchical numbered format
  - Task format: `- [ ] N.N [Description]`
  - Sub-task format: Indented `- [ ] N.N.N`
  - Config.yaml compliance: Pass
    - TDD order section at top; tests before implementation (Section 4 before Section 5)
    - Branch creation first (Section 1); PR creation last (Section 9)
    - GitHub issue creation task (Section 2) for nold-ai/specfact-cli
    - Version and changelog task (Section 8) before PR; patch bump and CHANGELOG sync
    - Quality gates, documentation tasks present
- **specs Format**: Pass (Given/When/Then in specs/sprint-planning/spec.md)
- **design.md Format**: Pass (sequence, contract enforcement, fallback documented)
- **Config.yaml Compliance**: Pass

## OpenSpec Validation

- **Status**: Pass
- **Validation Command**: `openspec validate sprint-planning-capacity-commitment-support --strict`
- **Issues Found**: 0
- **Issues Fixed**: 0

## Recommended Improvements Applied

1. **GitHub issue mandatory**: Issue #170 created in nold-ai/specfact-cli; proposal Source Tracking updated.
2. **Patch version and changelog**: Task 8 bumps patch version, syncs pyproject.toml/setup.py/src __init__.py, and adds CHANGELOG.md entry.
3. **TDD order**: TDD/SDD section at top of tasks.md; Section 4 (tests first, expect failure) before Section 5 (implement until tests pass).
4. **Backlog harmonization**: Sprint planning is under `specfact backlog sprint-summary`; no top-level `specfact sprint` command.

## Validation Artifacts

- No temporary workspace used (dry-run analysis only).
- Change directory: `openspec/changes/sprint-planning-capacity-commitment-support/`
