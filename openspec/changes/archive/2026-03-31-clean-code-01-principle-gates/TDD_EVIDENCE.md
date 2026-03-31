# TDD Evidence: clean-code-01-principle-gates

## Red phase — failing tests before implementation

**Timestamp**: 2026-03-31T~10:30 UTC (worktree session)

**Command**:
```bash
hatch test -- tests/unit/specfact_cli/test_clean_code_principle_gates.py -v
```

**Result**: 10 failed, 1 skipped

```
FAILED test_agents_md_references_clean_code_categories
FAILED test_claude_md_references_clean_code_categories
FAILED test_clean_code_mdc_references_seven_principles
FAILED test_clean_code_mdc_references_canonical_skill
FAILED test_copilot_instructions_exists_and_references_charter
FAILED test_agents_md_documents_clean_code_compliance_gate
FAILED test_claude_md_documents_clean_code_compliance_gate
FAILED test_clean_code_mdc_documents_phase_a_loc_thresholds
FAILED test_clean_code_mdc_mentions_nesting_and_parameter_checks
FAILED test_clean_code_mdc_documents_phase_b_as_deferred
SKIPPED test_copilot_instructions_does_not_duplicate_full_charter
```

**Failure summary**: AGENTS.md and CLAUDE.md had no references to `naming`, `kiss`,
`yagni`, `dry`, or `solid`. `.cursor/rules/clean-code-principles.mdc` did not mention
the 7-principle charter categories, Phase A thresholds, or Phase B deferral.
`.github/copilot-instructions.md` did not exist.

## Implementation

```text
Files changed:

1. `.cursor/rules/clean-code-principles.mdc` — rewrote as an alias surface referencing
   the canonical charter in `nold-ai/specfact-cli-modules`; added principle-to-category
   table, Phase A LOC thresholds (>80 / >120), nesting-depth and parameter-count notes,
   explicit Phase B deferral.

2. `AGENTS.md` — added **Clean-Code Review Gate** section listing all 5 review categories
   (`naming`, `kiss`, `yagni`, `dry`, `solid`) with Phase A threshold table.

3. `CLAUDE.md` — added identical **Clean-Code Review Gate** section.

4. `.github/copilot-instructions.md` — created as a lightweight alias (≤ 30 lines)
   referencing the canonical charter without duplicating it.
```

## Green phase — passing tests after implementation

**Timestamp**: 2026-03-31T~10:35 UTC

**Command**:
```bash
hatch test -- tests/unit/specfact_cli/test_clean_code_principle_gates.py -v
```

**Result**: 11 passed in 0.23s

```
PASSED test_agents_md_references_clean_code_categories
PASSED test_claude_md_references_clean_code_categories
PASSED test_clean_code_mdc_references_seven_principles
PASSED test_clean_code_mdc_references_canonical_skill
PASSED test_copilot_instructions_exists_and_references_charter
PASSED test_copilot_instructions_does_not_duplicate_full_charter
PASSED test_agents_md_documents_clean_code_compliance_gate
PASSED test_claude_md_documents_clean_code_compliance_gate
PASSED test_clean_code_mdc_documents_phase_a_loc_thresholds
PASSED test_clean_code_mdc_mentions_nesting_and_parameter_checks
PASSED test_clean_code_mdc_documents_phase_b_as_deferred
```

## Quality gates

All pre-commit gates passed:

- `hatch run format` — 1 file reformatted (test file), 0 remaining errors
- `hatch run type-check` — 0 errors, warnings only (pre-existing)
- `hatch run lint` — 10.00/10 pylint, all checks passed
- `hatch run yaml-lint` — clean
- `hatch run contract-test` — no modified files (no production code changes; cached pass)
- `hatch run smart-test` — no changed files mapped to tests (instruction-surface-only change)
