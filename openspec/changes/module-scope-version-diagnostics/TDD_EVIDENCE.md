# TDD Evidence

## Failing Before

- `hatch run pytest tests/unit/specfact_cli/registry/test_module_dependencies.py::test_validate_module_dependencies_detects_version_mismatch tests/unit/registry/test_module_installer.py::test_install_module_rejects_existing_bundle_dependency_version_mismatch tests/unit/modules/module_registry/test_commands.py::test_doctor_reports_effective_and_shadowed_duplicate_modules -q`
  - Result: FAIL (`3 failed`) before production edits.
  - Failures: `_validate_module_dependencies` rejected the new version map argument; install accepted an out-of-range existing dependency; `module doctor` did not exist.

## Passing After

- `hatch run pytest tests/unit/specfact_cli/registry/test_module_dependencies.py::test_validate_module_dependencies_detects_version_mismatch tests/unit/registry/test_module_installer.py::test_install_module_rejects_existing_bundle_dependency_version_mismatch tests/unit/modules/module_registry/test_commands.py::test_doctor_reports_effective_and_shadowed_duplicate_modules -q`
  - Result: PASS (`3 passed`).
- `hatch run pytest tests/unit/specfact_cli/registry/test_module_dependencies.py tests/unit/registry/test_module_installer.py tests/unit/modules/module_registry/test_commands.py -q`
  - Result: PASS (`96 passed`).

## Quality Gates

- `hatch run format`
  - Result: PASS (`All checks passed!`).
- `openspec validate module-scope-version-diagnostics --strict`
  - Result: PASS.
- `basedpyright src/specfact_cli/modules/module_registry/src/commands.py src/specfact_cli/registry/module_installer.py src/specfact_cli/registry/module_packages.py src/specfact_cli/registry/module_state.py tests/unit/modules/module_registry/test_commands.py tests/unit/registry/test_module_installer.py tests/unit/specfact_cli/registry/test_module_dependencies.py`
  - Result: PASS (`0 errors`, existing pytest monkeypatch typing warnings only).
- `hatch run specfact code review run --json --out .specfact/code-review.changed.json --scope changed`
  - Result: PASS (`0 blocking`, 17 warning-only findings).
  - Warning disposition: remaining findings are pre-existing local patterns in touched modules (parameter-count helpers, duplicate Typer validator shapes, existing naming heuristics, and legacy helper exposure). They were not expanded by this change except the validated dependency complexity, which was refactored before the passing review run.

## Real-World Tmp Smoke

- Created a temporary git repo with project module `nold-ai/specfact-codebase` version `0.41.0` and isolated user-scope module `nold-ai/specfact-codebase` version `0.40.0`.
  - Command: `hatch run env HOME=<tmp-home> specfact module doctor nold-ai/specfact-codebase --repo <tmp-repo>`
  - Result: PASS. Output showed project `0.41.0` as `effective`, user `0.40.0` as `shadowed`, and recovery command `specfact module uninstall nold-ai/specfact-codebase --scope user`.
- Created a temporary install root with existing dependency `nold-ai/dep` version `1.0.0` and installed a local tarball declaring `bundle_dependencies: [{id: nold-ai/dep, version: ">=2.0.0"}]` through the worktree installer.
  - Command: `hatch run python <tmp installer smoke>`
  - Result: PASS. Install failed with `Dependency nold-ai/dep requires >=2.0.0, but installed version is 1.0.0. Reinstall or upgrade the dependency in the same module scope.`

## Known Gate Caveat

- `hatch run lint`
  - Result: FAIL on repository-wide pre-existing `JsonType` basedpyright errors in `src/specfact_cli/adapters/ado.py`, `src/specfact_cli/adapters/github.py`, and `src/specfact_cli/validators/change_proposal_integration.py`.
  - Scoped basedpyright for this change passes with 0 errors.
