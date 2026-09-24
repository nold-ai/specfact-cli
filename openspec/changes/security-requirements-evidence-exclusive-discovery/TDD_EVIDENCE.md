# TDD Evidence: security-requirements-evidence-exclusive-discovery

## Failing-before

- **Command**: `hatch run pytest tests/unit/registry/test_module_discovery.py::test_exclusive_module_roots_reject_project_and_user_shadowing tests/unit/scripts/test_requirements_evidence_delivery_gate.py::test_failed_command_writes_missing_diagnostic_reports_and_exports_fixture_roots tests/unit/workflows/test_requirements_evidence_delivery_workflow.py::test_required_requirements_context_is_pull_request_only -q`
- **Result**: 2 failed, 1 passed.
- **Evidence**: discovery selected the repository-local same-identity module instead of the explicit fixture, and the adapter did not set an exclusive-discovery control.

## Passing-after

- **Command**: `hatch run pytest tests/unit/registry/test_module_discovery.py tests/unit/scripts/test_requirements_evidence_delivery_gate.py tests/unit/workflows/test_requirements_evidence_delivery_workflow.py -q`
- **Result**: 49 passed, 4 skipped because the optional pinned fixture checkout is unavailable.
- **Evidence**: exclusive discovery retained the bundled root and verified explicit root while excluding project, user, marketplace, custom, and legacy roots; adapter and workflow contracts require the control.

## Quality gates

- `hatch run format`, `hatch run type-check`, and `hatch run lint` passed. BasedPyright reported the repository's existing warning baseline with 0 errors; Ruff reported no findings.
- `hatch run yaml-lint` completed with pre-existing errors in archived Requirements evidence and the active Requirements 07 evidence ledger; no changed YAML file produced a finding.
- `hatch run openspec validate security-requirements-evidence-exclusive-discovery --strict`, `hatch run python scripts/check_reproducible_delivery.py`, and `uv lock --check` passed.
- Semgrep SAST and its baseline gate passed with 0 findings; Bandit reported no medium/high findings.
- Changed-scope `specfact code review run` passed with no findings after installing its declared BasedPyright and Pylint review tools.
- `hatch run contract-test` used the valid cached baseline. `hatch run smart-test` ran the full suite but reported two unrelated missing fixture-package imports (`specfact_backlog` and `specfact_spec`); the 49-test focused affected-scope suite remained green.

## Internal wiki follow-up

The sibling `specfact-cli-internal` checkout is unavailable in this environment. After it is available, add or update `wiki/sources/security-requirements-evidence-exclusive-discovery.md` and run `python3 scripts/wiki_rebuild_graph.py` from that repository root.
