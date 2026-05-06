# Change Validation: cli-val-06-copilot-test-generation

- **Validated on (UTC):** 2026-02-19T12:00:00Z
- **Workflow:** /wf-validate-change (proposal-stage dry-run validation)
- **Strict command:** `openspec validate cli-val-06-copilot-test-generation --strict`
- **Result:** PASS

## Scope Summary

- **New capabilities:** copilot-scenario-generation
- **Modified capabilities:** none
- **Declared dependencies:** cli-val-01-behavior-contract-standard (#279) -- hard blocker; cli-val-05-ci-integration (#283) -- soft dependency
- **Downstream dependents:** none
- **Proposed affected code paths:**
  - `resources/prompts/cli-scenario-generation.j2` (new Jinja2 prompt template)
  - `specfact generate test-prompt` workflow (extend to detect CLI commands)
  - `docs/` (new contributor page on copilot-driven scenario authoring)

## Format Validation

- **proposal.md Format**: PASS
  - Title format: Correct (`# Change: Copilot Test Generation for CLI Scenarios`)
  - Required sections: All present (Why, What Changes, Capabilities, Impact)
  - "What Changes" format: Correct (uses NEW/EXTEND markers with bullet list)
  - "Capabilities" section: Present (one capability: `copilot-scenario-generation`)
  - "Impact" format: Correct (lists Affected specs, Affected code, Integration points, Documentation impact)
  - Source Tracking section: Present (GitHub Issue #284, repository nold-ai/specfact-cli)
- **tasks.md Format**: PASS
  - Section headers: Correct (hierarchical numbered format: `## 1.` through `## 8.`)
  - Task format: Correct (`- [ ] 1.1 [Description]`)
  - Sub-task format: Correct (`- [ ] 1.1.1 [Description]`)
  - TDD order enforced section: Present at top
  - Git worktree creation: First task (`## 1.`)
  - Blocker verification: Task 1.1.6 verifies cli-val-01 is merged before starting (correct -- hard blocker)
  - PR creation: Last implementation task (`## 8. Delivery`, task 8.4)
  - Post-merge cleanup: Present
  - Quality gate tasks: Present (`## 6.` -- includes format, type-check, lint, contract-test, smart-test)
  - Version and changelog tasks: Present (`## 7.`)
  - Validation with example commands: Present (`## 5.` -- tests template against 3 command types)
  - Note: Task 1.1.6 correctly verifies only cli-val-01 (hard blocker) and does not require cli-val-05 (soft dependency). This is correct per CHANGE_ORDER.md.
  - Note: No explicit worktree bootstrap pre-flight tasks. Minor gap, non-blocking.
- **specs Format**: PASS
  - Given/When/Then format: Verified across all 5 scenarios in `specs/copilot-scenario-generation/spec.md`
  - Three requirements defined: CLI Scenario Prompt Template (3 scenarios), Generate Test-Prompt Integration (1 scenario), Convention Enforcement Documentation (1 scenario)
  - All scenarios use GIVEN/WHEN/THEN/AND structure correctly
- **design.md Format**: PASS
  - Context section: Present
  - Goals / Non-Goals: Present (4 goals, 3 non-goals)
  - Decisions: Present (4 decisions documented)
  - Risks / Trade-offs: Present (3 risks with mitigations)
  - Migration Plan: Present (4-step plan)
  - Open Questions: Present (2 questions)

## Dependency and Integration Review

- **CHANGE_ORDER.md consistency**: PASS
  - CHANGE_ORDER.md row: `cli-val | 06 | cli-val-06-copilot-test-generation | #284 | #279 (soft: #283)`
  - Hard blocked by: #279 (cli-val-01)
  - Soft dependency: #283 (cli-val-05) -- for enforcement convention
  - Wave 1.5 position: After cli-val-01 (hard blocker); parallel with cli-val-03
- **GitHub Issue consistency**: PASS
  - Issue #284 is OPEN, title "[Change] Copilot Test Generation for CLI Scenarios"
  - Issue body states: `**Blocked by**: #279 (cli-val-01). Soft dependency: #283 (cli-val-05) for enforcement.`
  - Labels: enhancement, change-proposal
- **Cross-artifact dependency consistency**: PASS
  - Proposal states hard blocker: cli-val-01 (schema the templates generate); soft dependency: cli-val-05 (enforcement)
  - CHANGE_ORDER.md shows hard blocker: #279; soft: #283
  - GitHub issue #284 states: Blocked by #279; soft dependency #283
  - tasks.md task 1.1.6 verifies cli-val-01 only (correct -- only hard blocker needs verification)
  - All four sources agree on hard vs soft dependency distinction

## Breaking-Change Analysis

- **Breaking changes detected:** 0
- **Interface changes:** Minimal. This change extends the existing `specfact generate test-prompt` workflow to detect CLI commands and offer a new template option. The extension is additive -- existing template options remain unchanged. The new prompt template in `resources/prompts/` is a new file.
- **Risk assessment:** No breaking-change risk. The only existing code touched is the `generate test-prompt` workflow, and the modification is purely additive (new option detection, not modification of existing behavior).

## Impact Assessment

- **Impact Level:** Low
- **Code Impact:** Minor extension to `generate test-prompt` workflow (additive detection logic). New Jinja2 prompt template. No other production CLI code changes.
- **Test Impact:** New test file in `tests/unit/`. No changes to existing tests.
- **Documentation Impact:** New contributor page in `docs/` for copilot-driven scenario authoring. Convention documentation for requiring scenario files with CLI command changes.
- **Release Impact:** Patch/Minor (additive only, no breaking changes)

## Validation Outcome

- Required artifacts are present: `proposal.md`, `design.md`, `specs/copilot-scenario-generation/spec.md`, `tasks.md`.
- All format checks pass with minor non-blocking observations noted.
- Dependency declarations are consistent across proposal, CHANGE_ORDER.md, GitHub issue #284, and tasks.md blocker verification. Hard vs soft dependency distinction is correctly maintained.
- No breaking changes detected.
- Change is ready for implementation-phase intake once cli-val-01 (#279) is implemented and merged. Soft dependency on cli-val-05 (#283) does not block implementation.
