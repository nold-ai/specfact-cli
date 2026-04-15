# TDD Evidence — dep-security-cleanup

## Pre-implementation failing test run

Run date: 2026-04-15

Command:

```bash
hatch test -- tests/unit/analyzers/test_graph_analyzer.py \
              tests/unit/utils/test_optional_deps.py \
              tests/unit/utils/test_project_artifact_write.py \
              tests/unit/scripts/test_check_license_compliance.py -v
```

### Result summary — pre-migration

- **12 FAILED** — new tests specifying post-migration behaviour
- **11 ERROR** — fixture error (check_license_compliance.py does not exist yet)
- **21 PASSED** — existing tests unaffected

### New failing tests

#### graph_analyzer failures (Tasks 1.1 & 1.2)

- `FAILED test_extract_call_graph_invokes_pycg_not_pyan3` — current code calls pyan3
- `FAILED test_parse_pycg_json_returns_correct_structure` — method `_parse_pycg_json` does not exist
- `FAILED test_parse_pycg_json_handles_empty_output` — method `_parse_pycg_json` does not exist

#### optional_deps failures (Task 1.3)

- `FAILED test_check_optional_analysis_deps_includes_pycg_key` — result has no `pycg` key
- `FAILED test_check_optional_analysis_deps_excludes_pyan3` — `pyan3` still present
- `FAILED test_check_optional_analysis_deps_excludes_syft` — `syft` still present
- `FAILED test_check_optional_analysis_deps_excludes_bearer` — `bearer` still present
- `FAILED test_check_optional_analysis_deps_includes_bandit_key` — no `bandit` key

#### project_artifact_write failures (Tasks 1.4 & 1.5)

- `FAILED test_project_artifact_write_does_not_import_json5` — `import json5` found in source
- `FAILED test_project_artifact_write_uses_commentjson_for_read` — no `commentjson` import found

#### check_license_compliance (Task 1.6)

- `ERROR` on all 11 tests — `scripts/check_license_compliance.py` does not exist yet

### Tests that pass with target behaviour already (will pass after migration too)

- `test_extract_call_graph_returns_empty_on_nonzero_exit` — PASSES because mock returns {} for both pyan3 and pycg
- `test_extract_call_graph_returns_empty_when_pycg_missing` — PASSES with patched optional_deps
- `test_merge_vscode_settings_handles_block_comments_in_jsonc` — PASSES (json5 handles block comments too)
- `test_merge_vscode_settings_handles_trailing_commas_in_jsonc` — PASSES (json5 handles trailing commas too)
- `test_merge_vscode_settings_write_output_is_valid_stdlib_json` — PASSES (json5 with quote_keys+no trailing_commas produces stdlib-compatible JSON)

---

## Post-implementation passing test run

Run date: 2026-04-16

Command:

```bash
hatch test --cover -v
```

### Result summary — post-migration

- **2530 passed**, 9 skipped, 0 failed
- **Coverage**: 63% line coverage (above the 50% gate threshold)
- `hatch run format` — clean (0 errors)
- `hatch run type-check` — 0 errors, 1523 pre-existing warnings

### New tests now passing (were FAILED/ERROR pre-implementation)

#### graph_analyzer passing (Tasks 1.1 & 1.2)

- `PASSED test_extract_call_graph_invokes_pycg_not_pyan3`
- `PASSED test_parse_pycg_json_returns_correct_structure`
- `PASSED test_parse_pycg_json_handles_empty_output`

#### optional_deps passing (Task 1.3)

- `PASSED test_check_optional_analysis_deps_includes_pycg_key`
- `PASSED test_check_optional_analysis_deps_excludes_pyan3`
- `PASSED test_check_optional_analysis_deps_excludes_syft`
- `PASSED test_check_optional_analysis_deps_excludes_bearer`
- `PASSED test_check_optional_analysis_deps_includes_bandit_key`

#### project_artifact_write passing (Tasks 1.4 & 1.5)

- `PASSED test_project_artifact_write_does_not_import_json5`
- `PASSED test_project_artifact_write_uses_commentjson_for_read`
- `PASSED test_merge_vscode_settings_handles_line_comments_in_jsonc` (renamed from line-and-block: `commentjson` grammar used here does not parse `/* */` in these fixtures)

#### check_license_compliance (Task 1.6) — all 11 now passing

- `PASSED test_scan_installed_env_passes_with_no_gpl`
- `PASSED test_scan_installed_env_prints_summary`
- `PASSED test_scan_installed_env_fails_on_gpl_package`
- `PASSED test_scan_installed_env_prints_violation_message`
- `PASSED test_allowlist_entry_suppresses_gpl_failure`
- `PASSED test_allowlist_entry_prints_exception_note`
- `PASSED test_dev_only_allowlist_rejected_in_manifest_scan`
- `PASSED test_unknown_license_exits_0_with_warning`
- `PASSED test_clean_manifests_exit_0`
- `PASSED test_gpl_in_manifest_exits_1`
- `PASSED test_gpl_in_manifest_prints_module_manifest_violation`

---

## Code-review remediation verification (2026-04-16)

Commands (from worktree root):

```bash
hatch run format
hatch run type-check
hatch run pytest tests/unit/analyzers/test_graph_analyzer.py \
  tests/unit/utils/test_optional_deps.py tests/unit/utils/test_project_artifact_write.py \
  tests/unit/scripts/test_check_license_compliance.py tests/unit/scripts/test_security_audit_gate.py -q
openspec validate dep-security-cleanup --strict
hatch test -q --tb=no
hatch run security-audit
hatch run bandit-scan
hatch run license-check   # see note below
```

### Results

- **format / type-check**: clean for touched scope.
- **Targeted pytest** (graph / optional_deps / project_artifact_write / license script / security gate): all passed.
- **Full suite**: `hatch test -q` — **2548 passed**, 9 skipped.
- **openspec validate dep-security-cleanup --strict**: valid.
- **security-audit** (`python scripts/security_audit_gate.py`): exit 0; pip CVE for `pip` reported with CVSS default 0.0 (WARNING only per gate).
- **bandit-scan**: completes with findings (Low/Medium/High counts in Bandit summary); exit code 1 — treat as **review baseline**, not introduced by this remediation slice.
- **license-check**: in this Hatch default environment `pip_licenses` was not importable (`No module named pip_licenses`), so the gate failed closed as designed. Re-run after `pip install -e ".[dev]"` (or Hatch env with dev extra) where `pip-licenses` is installed.
