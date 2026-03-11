# TDD Evidence

## Pre-Implementation Failing Run

- Timestamp: 2026-03-06 21:46:54 CET
- Command:

```bash
hatch run pytest tests/unit/test_backlog_module_ownership_cleanup.py -q
```

- Result: failed as expected

### Failure Summary

- `test_core_repo_no_longer_ships_backlog_owned_command_surfaces`
  - Core still ships `modules/backlog-core`, `src/specfact_cli/commands/backlog_commands.py`, and `src/specfact_cli/groups/backlog_group.py`.
- `test_core_prompt_export_surface_excludes_backlog_prompts_and_templates`
  - Core still ships backlog prompt files under `resources/prompts/` and backlog templates under `resources/templates/backlog/`.
- `test_backlog_duplicate_overlap_tolerance_is_not_required`
  - `specfact_cli.registry.module_packages._is_expected_duplicate_extension(...)` still explicitly tolerates split backlog ownership.

## Post-Implementation Passing Run

- Timestamp: 2026-03-06 21:59:58 CET
- Command:

```bash
hatch run pytest tests/unit/test_backlog_module_ownership_cleanup.py tests/unit/utils/test_ide_setup.py tests/integration/test_command_package_runtime_validation.py -q
```

- Result: passed

### Passing Summary

- Ownership-boundary tests now pass:
  - core no longer ships `modules/backlog-core`
  - core no longer ships backlog command shim/group files
  - core no longer exports backlog prompt/template resources or prompt ids
  - registry merge logic no longer tolerates split backlog overlap
- Regression slice passes for:
  - core IDE prompt export behavior
  - temp-home command-package runtime validation with marketplace bundles

### OpenSpec Validation

- Command:

```bash
openspec validate backlog-module-ownership-cleanup --strict
```

- Result: passed
