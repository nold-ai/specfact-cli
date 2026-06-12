# TDD Evidence: tooling-spaced-env-pythonpath

## Failing evidence

- **Focused regression**: `hatch run pytest tests/unit/packaging/test_core_package_includes.py::test_hatch_gate_scripts_quote_pythonpath_interpreter_substitution -q` failed before production edits (`0 passed, 1 failed`) because `type-check` and `lint` used unquoted `--pythonpath $(python -c 'import sys; print(sys.executable)')`.
- **Mac reproduction**: `hatch run type-check` failed on 2026-06-09 because the configured script split the Hatch interpreter path under `Application Support`.

## Passing evidence

- **OpenSpec**: `hatch run openspec validate tooling-spaced-env-pythonpath --strict` passed.
- **Focused regression**: `hatch run pytest tests/unit/packaging/test_core_package_includes.py::test_hatch_gate_scripts_quote_pythonpath_interpreter_substitution -q` passed.
- **Pattern audit**: `rg -n -e "--pythonpath \\$\\(python -c" -e "pythonpath \\$\\(" -e "sys\\.executable\\)" pyproject.toml scripts src tests docs openspec/changes/tooling-spaced-env-pythonpath` found no remaining active unquoted `--pythonpath $(...)` gate script patterns.
- **Type gate**: `hatch run type-check` passed through the Hatch script on macOS with the interpreter path under `Application Support` (`0 errors`; existing basedpyright warning baseline remains).
- **Lint gate**: `hatch run lint` passed outside the Codex sandbox. The in-sandbox run reached pylint after ruff and basedpyright passed, then failed on a sandbox-only process-pool system call; the normal user-shell run passed.
- **YAML gate**: `hatch run yaml-lint` passed after wrapping the pre-existing long `docs/_config.yml` description line.
- **Review gate**: after installing `nold-ai/specfact-code-review` in user scope, `hatch run python scripts/pre_commit_code_review.py ...` passed outside the Codex sandbox with `overall_verdict='PASS_WITH_ADVISORY'`, `errors=0`, `warnings=19`, and `info=2`.
