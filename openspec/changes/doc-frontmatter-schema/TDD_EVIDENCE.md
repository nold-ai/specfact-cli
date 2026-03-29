# TDD Evidence for doc-frontmatter-schema

## Pre-Implementation Test Failure (Expected)

### Test Run: 2026-03-20 - Frontmatter Schema Tests

**Command:**
```bash
cd /home/dom/git/nold-ai/specfact-cli-worktrees/feature/doc-frontmatter-schema && python -m pytest tests/unit/scripts/test_doc_frontmatter/test_schema.py -v
```

**Result:** ✅ 11 tests failed as expected (TDD - no implementation yet)

**Failed Tests:**
- `TestFrontmatterParsing::test_valid_frontmatter_parsing` - parse_frontmatter function not implemented yet
- `TestFrontmatterParsing::test_missing_required_fields` - parse_frontmatter function not implemented yet
- `TestFrontmatterParsing::test_no_frontmatter` - parse_frontmatter function not implemented yet
- `TestOwnerResolution::test_path_like_owner_resolution` - resolve_owner function not implemented yet
- `TestOwnerResolution::test_known_token_resolution` - resolve_owner function not implemented yet
- `TestOwnerResolution::test_invalid_owner_resolution` - resolve_owner function not implemented yet
- `TestGlobPatternValidation::test_valid_glob_patterns` - validate_glob_patterns function not implemented yet
- `TestGlobPatternValidation::test_invalid_glob_patterns` - validate_glob_patterns function not implemented yet
- `TestFrontmatterSuggestions::test_suggest_frontmatter_template` - suggest_frontmatter function not implemented yet
- `TestExtractDocOwner::test_extract_valid_owner` - extract_doc_owner function not implemented yet
- `TestExtractDocOwner::test_extract_missing_owner` - extract_doc_owner function not implemented yet

**Status:** ✅ TDD workflow confirmed - tests fail before implementation

---

## Post-Implementation Test Success (To be added after implementation)

### Test Run: [Date] - Frontmatter Schema Tests (After Implementation)

**Command:**
```bash
cd /home/dom/git/nold-ai/specfact-cli-worktrees/feature/doc-frontmatter-schema && python -m pytest tests/unit/scripts/test_doc_frontmatter/test_schema.py -v
```

**Result:** [To be completed after implementation]

**Status:** [To be completed after implementation]

---

### Test Run: 2026-03-20 - Validation Logic Tests (Pre-Implementation)

**Command:**
```bash
cd /home/dom/git/nold-ai/specfact-cli-worktrees/feature/doc-frontmatter-schema && python -m pytest tests/unit/scripts/test_doc_frontmatter/test_validation.py -v
```

**Result:** ✅ 10 tests failed as expected (TDD - no implementation yet)

**Failed Tests:**
- `TestFileDiscovery::test_discover_docs_directory_files` - get_all_md_files function not implemented yet
- `TestFileDiscovery::test_exempt_files_exclusion` - get_all_md_files function not implemented yet
- `TestMissingDocOwnerDetection::test_missing_doc_owner_detection` - rg_missing_doc_owner function not implemented yet
- `TestMissingDocOwnerDetection::test_all_files_have_owner` - rg_missing_doc_owner function not implemented yet
- `TestValidationMainFunction::test_validation_with_valid_files` - validation_main function not implemented yet
- `TestValidationMainFunction::test_validation_with_invalid_files` - validation_main function not implemented yet
- `TestOwnerResolutionValidation::test_valid_owner_resolution` - validation_main function not implemented yet
- `TestOwnerResolutionValidation::test_invalid_owner_resolution` - validation_main function not implemented yet
- `TestFixHintGeneration::test_fix_hint_for_missing_frontmatter` - validation_main function not implemented yet
- `TestFixHintGeneration::test_fix_hint_for_invalid_owner` - validation_main function not implemented yet

**Status:** ✅ TDD workflow confirmed - validation tests fail before implementation

---

### Test Run: 2026-03-20 - Integration Tests (Pre-Implementation)

**Command:**
```bash
cd /home/dom/git/nold-ai/specfact-cli-worktrees/feature/doc-frontmatter-schema && python -m pytest tests/integration/scripts/test_doc_frontmatter/test_integration.py -v
```

**Result:** ✅ 9 tests failed as expected, 1 error (benchmark fixture) - TDD confirmed

**Failed Tests:**
- `TestEndToEndWorkflow::test_complete_validation_workflow` - validation_main function not implemented yet
- `TestEndToEndWorkflow::test_validation_with_all_valid_files` - validation_main function not implemented yet
- `TestMultipleFileScenarios::test_large_number_of_files` - validation_main function not implemented yet
- `TestMultipleFileScenarios::test_nested_directory_structure` - validation_main function not implemented yet
- `TestPerformance::test_memory_usage_with_large_files` - validation_main function not implemented yet
- `TestCommandLineInterface::test_cli_with_fix_hint_flag` - validation_main function not implemented yet
- `TestCommandLineInterface::test_cli_help_output` - validation_main function not implemented yet
- `TestRealWorldScenarios::test_mixed_exempt_and_regular_files` - validation_main function not implemented yet
- `TestRealWorldScenarios::test_complex_tracking_patterns` - validation_main function not implemented yet

**Error:**
- `TestPerformance::test_execution_time_with_many_files` - fixture 'benchmark' not found (expected - benchmark fixture not available)

**Status:** ✅ TDD workflow confirmed - integration tests fail before implementation

---

## Post-Implementation (2026-03-29)

**Commands:**
```bash
cd /home/dom/git/nold-ai/specfact-cli-worktrees/feature/doc-frontmatter-schema
hatch run pytest tests/unit/scripts/test_doc_frontmatter tests/integration/scripts/test_doc_frontmatter -q
```

**Result:** 31 passed (unit + integration). `last_reviewed` validation accepts YAML date objects via `isoformat()`. Rollout uses `docs/.doc-frontmatter-enforced`; default CLI skips when file missing; `--all-docs` validates entire `docs/` tree.

**Status:** ✅ Green

---

## Quality gates (2026-03-30)

Recorded for `tasks.md` §5 checklist evidence (commands run from the feature worktree).

**Timestamp:** 2026-03-30 (local) — see session `date` when re-running.

**Commands (success unless noted):**

| Step | Command | Result summary |
|------|---------|------------------|
| Format | `hatch run format` | Ruff format + fix applied; exit 0 |
| Type check | `hatch run type-check` | basedpyright strict; exit 0 |
| Lint | `hatch run lint` | Full lint suite; exit 0 |
| Contract | `hatch run contract-test` | Contract-first validation; exit 0 |
| Tests | `hatch run smart-test-full` or `hatch test --cover -v` | Full suite green |
| OpenSpec | `openspec validate doc-frontmatter-schema --strict` | Validation passed |

**Note:** Re-run the rows above after substantive edits and refresh this table if outputs change.

---

## PR Orchestrator Parallelization Delta (2026-03-30)

### Pre-Implementation Test Failure (Expected)

**Timestamp:** 2026-03-30T01:09:14+02:00

**Command:**
```bash
cd /home/dom/git/nold-ai/specfact-cli-worktrees/feature/doc-frontmatter-schema
/home/dom/git/nold-ai/specfact-cli/.venv/bin/pytest tests/unit/specfact_cli/registry/test_signing_artifacts.py -q -k 'independent_jobs_do_not_wait_for_tests or quality_gates_still_depends_on_tests_for_coverage'
```

**Result:** ✅ 5 tests failed as expected before workflow changes; 1 coverage-dependency guard test passed.

**Failure summary:**
- `compat-py311` currently depends on `changes` and `tests` instead of `changes` and `verify-module-signatures`
- `contract-first-ci` currently depends on `changes`, `tests`, and `compat-py311`
- `type-checking` currently depends on `changes` and `tests`
- `linting` currently depends on `changes` and `tests`
- `cli-validation` currently depends on `changes` and `contract-first-ci`

**Status:** ✅ TDD workflow confirmed for the PR-orchestrator dependency delta

### Post-Implementation Test Success

**Command:**
```bash
cd /home/dom/git/nold-ai/specfact-cli-worktrees/feature/doc-frontmatter-schema
/home/dom/git/nold-ai/specfact-cli/.venv/bin/pytest tests/unit/specfact_cli/registry/test_signing_artifacts.py -q -k 'independent_jobs_do_not_wait_for_tests or quality_gates_still_depends_on_tests_for_coverage'
/home/dom/git/nold-ai/specfact-cli/.venv/bin/pytest tests/unit/scripts/test_doc_frontmatter tests/integration/scripts/test_doc_frontmatter -q
```

**Result:** ✅ Workflow dependency tests passed (`6 passed, 20 deselected`) and doc-frontmatter
regression slice remained green (`34 passed`).

**Passing summary:**
- `compat-py311`, `contract-first-ci`, `type-checking`, `linting`, and `cli-validation` now depend
  on `changes` plus `verify-module-signatures`
- `quality-gates` still depends on `tests` because it consumes coverage artifacts
- Existing doc-frontmatter unit/integration coverage remained unchanged by the workflow delta

**Status:** ✅ Delta implemented and verified
