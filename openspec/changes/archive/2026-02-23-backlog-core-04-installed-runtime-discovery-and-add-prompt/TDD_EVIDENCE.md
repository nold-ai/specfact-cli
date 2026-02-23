# TDD Evidence: backlog-core-04-installed-runtime-discovery-and-add-prompt

## Pre-implementation failing run

- **Timestamp**: 2026-02-23T09:25:01+01:00
- **Command**:
  - `hatch run pytest tests/unit/specfact_cli/registry/test_module_packages.py::test_get_modules_roots_includes_cwd_modules_when_present tests/unit/utils/test_ide_setup.py::test_specfact_commands_includes_backlog_add_prompt -q`
- **Result**: Failed (expected)
- **Failure summary**:
  - `get_modules_roots()` did not include `cwd/modules`.
  - `SPECFACT_COMMANDS` did not include `specfact.backlog-add`.

## Post-implementation passing run

- **Timestamp**: 2026-02-23T09:26:02+01:00
- **Command**:
  - `hatch run pytest tests/unit/specfact_cli/registry/test_module_packages.py::test_get_modules_roots_includes_cwd_modules_when_present tests/unit/utils/test_ide_setup.py::test_specfact_commands_includes_backlog_add_prompt -q`
- **Result**: Pass
- **Summary**:
  - `get_modules_roots()` now includes `cwd/modules` when present.
  - IDE setup command list includes `specfact.backlog-add`.
