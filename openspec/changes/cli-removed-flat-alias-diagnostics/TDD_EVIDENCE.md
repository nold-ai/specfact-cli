# TDD Evidence: cli-removed-flat-alias-diagnostics

## Failing-before

- **Timestamp**: 2026-06-09 23:26:54 CEST
- **Command**: `hatch run python -m pytest tests/integration/test_category_group_routing.py`
- **Result**: Failed as expected before production edits.
- **Summary**: Seven removed flat aliases (`validate`, `plan`, `analyze`, `drift`, `repro`, `sync`, `migrate`) emitted shadowed module diagnostics when the regression fixture simulated both project-scope and user-scope marketplace module copies.

## Passing-after

- **Timestamp**: 2026-06-09 23:28:00 CEST
- **Command**: `hatch run python -m pytest tests/integration/test_category_group_routing.py`
- **Result**: Passed, 10 tests.
- **Summary**: Removed flat aliases now produce ordinary unknown-command behavior without installed, disabled, skipped, or shadowed module diagnostics.

## Targeted command and registry suite

- **Timestamp**: 2026-06-09 23:32:42 CEST
- **Command**: `hatch run python -m pytest tests/integration/test_category_group_routing.py tests/unit/specfact_cli/registry/test_command_registry.py tests/unit/registry/test_category_groups.py tests/integration/test_command_package_runtime_validation.py`
- **Result**: Passed, 27 tests; 2 skipped because the companion `specfact-cli-modules` packages checkout is unavailable.
- **Summary**: Removed flat aliases stay unregistered, canonical grouped commands remain discoverable when installed, and command registry help behavior stays stable.

## External validation checkout

- **Timestamp**: 2026-06-09 23:30:11-23:30:20 CEST
- **Working directory**: `<validation-workspace>/zettelkasten-mcp`
- **Commands**:
  - `python -m specfact_cli validate --help`
  - `python -m specfact_cli plan --help`
  - `python -m specfact_cli code validate --help`
- **Result**: `validate` and `plan` returned `No such cmd` without module shadow/install diagnostics; canonical `code validate --help` rendered grouped command help.

## Static and quality gates

- **Timestamp**: 2026-06-09 23:33:11-23:33:52 CEST
- **Passed**:
  - `hatch run format`
  - `hatch run basedpyright --level error --pythonpath "<hatch-env under macOS 'Application Support'>/bin/python"`
  - `hatch run ruff check .`
  - `hatch run ruff format . --check`
  - `hatch run pylint src/specfact_cli/cli.py tests/integration/test_category_group_routing.py tests/unit/registry/test_category_groups.py`
  - `hatch run openspec validate cli-removed-flat-alias-diagnostics --strict`
  - `hatch run type-check`
  - `hatch run lint` outside the Codex sandbox
  - `hatch run yaml-lint`
  - `hatch run python scripts/pre_commit_code_review.py ...` outside the Codex sandbox after installing `nold-ai/specfact-code-review` in user scope (`PASS_WITH_ADVISORY`, `errors=0`)
- **Resolved follow-up**: the macOS Hatch script quote failure is covered by `tooling-spaced-env-pythonpath`.
- **Post-install regression caught and fixed**: after installing `nold-ai/specfact-code-review` in user scope, `hatch run python -m pytest ...` exposed that missing canonical `backlog` diagnostics fell through to Typer's raw `No such command` path. The root Click group now patches both `get_command` and `resolve_command`, preserving actionable install guidance for still-supported canonical groups while keeping removed flat aliases out of module diagnostics.
- **Final targeted tests**: `hatch run python -m pytest tests/integration/test_category_group_routing.py tests/unit/specfact_cli/registry/test_command_registry.py tests/unit/registry/test_category_groups.py tests/integration/test_command_package_runtime_validation.py tests/unit/packaging/test_core_package_includes.py::test_hatch_gate_scripts_quote_pythonpath_interpreter_substitution` passed (`28 passed`, `2 skipped` for missing companion package checkout).
- **Release hygiene**:
  - Bumped the four canonical version artifacts from `0.47.4` to `0.47.5`: `pyproject.toml`, `setup.py`, `src/__init__.py`, and `src/specfact_cli/__init__.py`.
  - Added `CHANGELOG.md` entry `0.47.5` dated 2026-06-10.
  - `hatch run check-version-sources` passed.
  - `hatch run check-pypi-ahead` passed outside the Codex sandbox; local `0.47.5` is ahead of PyPI latest `0.47.3`.

## PR #606 review follow-up (2026-06-12)

- **Failing-before**: CI `Tests (Python 3.12)` and `Compatibility (Python 3.11)` failed on
  `tests/integration/test_core_slimming.py::test_stale_flat_shim_plan_exits_with_install_instructions`,
  a stale expectation that the removed `plan` alias still emits install guidance.
- **Fix**: removed flat aliases now print canonical grouped replacement guidance
  (`_REMOVED_FLAT_ALIAS_TO_CANONICAL` in `src/specfact_cli/cli.py`) across all three root
  resolution surfaces (`_RootCLIGroup`, the patched Typer root group, and the lazy delegate
  loader), satisfying the spec scenario "guidance to the canonical grouped command". The stale
  test was renamed to `test_stale_flat_shim_plan_exits_with_removed_alias_guidance` and asserts
  the new contract; the shadowed-module regression also asserts canonical guidance and tolerates
  unknown-command wording variants.
- **Passing-after**: `hatch run python -m pytest tests/integration/test_core_slimming.py tests/integration/test_category_group_routing.py tests/unit/registry/test_category_groups.py tests/unit/packaging/test_core_package_includes.py tests/unit/specfact_cli/registry/test_command_registry.py tests/integration/test_command_package_runtime_validation.py`
  passed (`45 passed, 2 skipped` for missing companion package checkout). `hatch run type-check`
  (0 errors), `hatch run lint` (pylint 10.00/10), and both strict OpenSpec validations passed.
- **Manual proof**: `python -m specfact_cli validate --help` and `plan --help` exit 1 with
  "No such command ... was removed. Use specfact code validate / specfact project ... instead"
  and no module install/disabled/skipped/shadowed diagnostics.
- **Hygiene**: host-specific absolute paths redacted from validation evidence files.
- **Release hygiene**: bumped the four canonical version artifacts from `0.47.5` to `0.47.6`
  and added the `CHANGELOG.md` entry `0.47.6` dated 2026-06-12 (per the packaged-artifact
  version gate); `hatch run check-version-sources` passed.

## Documentation alignment

- **Timestamp**: 2026-06-09 CEST
- **Searches**:
  - `docs`: `specfact (validate|plan|analyze|drift|repro|sync|migrate)`
  - `README.md`: `specfact (validate|plan|analyze|drift|repro|sync|migrate)`
  - repository-wide: `flat shim|flat alias|flat command|removed flat|shim removal`
- **Result**: Migration and command-reference docs already describe removed flat commands as removed. One stale live-doc sentence in `docs/validation-integration.md` still referred to `specfact validate`; it was updated to the canonical grouped validation path.
