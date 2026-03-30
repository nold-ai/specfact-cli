# TDD Evidence for ci-02-trustworthy-green-checks

## Pre-Implementation Test Failure (Expected)

### Test Run: 2026-03-30 - Pre-commit Review Report Failure Handling

**Command:**

```bash
cd /home/dom/git/nold-ai/specfact-cli
python3 -m pytest tests/unit/scripts/test_pre_commit_code_review.py -q -k 'missing_report or rejects_non_object_json'
```

**Result:** ✅ 2 tests failed as expected before implementation.

**Failure summary:**

- `test_main_missing_report_still_returns_exit_code_and_warns` failed because the hook did not
  create the `.specfact/` parent directory before invoking the subprocess and treated a missing
  review report as a non-fatal outcome.
- `test_print_summary_rejects_non_object_json` failed because malformed report content printed an
  error but still returned exit code `0`.

**Status:** ✅ TDD workflow confirmed for review-report enforcement hardening.

## Post-Implementation Test Success

### Test Run: 2026-03-30 - Hardened Review Report and Doc Frontmatter Validation Slice

**Commands:**

```bash
cd /home/dom/git/nold-ai/specfact-cli
python3 -m pytest tests/unit/scripts/test_pre_commit_code_review.py -q -k 'missing_report or rejects_non_object_json or count_findings_by_severity'
python3 -m pytest tests/unit/scripts/test_doc_frontmatter/test_validation.py -q -k 'fix_hint_for_missing_frontmatter or fix_hint_for_invalid_owner'
python3 -m pytest tests/integration/scripts/test_doc_frontmatter/test_integration.py -q -k 'complete_validation_workflow or validation_with_all_valid_files or cli_with_fix_hint_flag'
```

**Result:** ✅ All targeted tests passed after implementation.

**Passing summary:**

- `scripts/pre_commit_code_review.py` now creates the review-report directory, validates
  `.specfact/code-review.json` with Pydantic models, and fails non-zero when the report is missing
  or malformed.
- `scripts/check_doc_frontmatter.py` now preserves fallback discovery behavior while emitting
  debug-level diagnostics when `parse_frontmatter(file_path)` raises file/YAML errors.
- The CLI root command now propagates validation exit codes correctly, so `--fix-hint` failures do
  not return a false green status.
- Helper fixtures and tests now assert the implemented required fields and valid owner behavior.

**Status:** ✅ Remediation implemented and verified.
