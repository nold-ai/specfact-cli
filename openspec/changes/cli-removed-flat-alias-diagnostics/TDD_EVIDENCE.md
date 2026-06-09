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
- **Working directory**: `/Users/dom/git/specfact-validation/zettelkasten-mcp`
- **Commands**:
  - `python -m specfact_cli validate --help`
  - `python -m specfact_cli plan --help`
  - `python -m specfact_cli code validate --help`
- **Result**: `validate` and `plan` returned `No such cmd` without module shadow/install diagnostics; canonical `code validate --help` rendered grouped command help.

## Static and quality gates

- **Timestamp**: 2026-06-09 23:33:11-23:33:52 CEST
- **Passed**:
  - `hatch run format`
  - `hatch run basedpyright --level error --pythonpath "/Users/dom/Library/Application Support/hatch/env/virtual/specfact-cli/J21BTy96/specfact-cli/bin/python"`
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

## Documentation alignment

- **Timestamp**: 2026-06-09 CEST
- **Searches**:
  - `docs`: `specfact (validate|plan|analyze|drift|repro|sync|migrate)`
  - `README.md`: `specfact (validate|plan|analyze|drift|repro|sync|migrate)`
  - repository-wide: `flat shim|flat alias|flat command|removed flat|shim removal`
- **Result**: Migration and command-reference docs already describe removed flat commands as removed. One stale live-doc sentence in `docs/validation-integration.md` still referred to `specfact validate`; it was updated to the canonical grouped validation path.
