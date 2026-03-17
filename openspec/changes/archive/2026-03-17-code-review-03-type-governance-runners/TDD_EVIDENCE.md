# TDD Evidence: code-review-03-type-governance-runners

## Failing test evidence

Command:

```bash
hatch run python -m pytest tests/unit/specfact_code_review/tools/test_basedpyright_runner.py tests/unit/specfact_code_review/tools/test_pylint_runner.py -v
```

Observed failure:

```text
ImportError while importing test module '.../tests/unit/specfact_code_review/tools/test_basedpyright_runner.py'
E   ModuleNotFoundError: No module named 'specfact_code_review.tools.basedpyright_runner'

ImportError while importing test module '.../tests/unit/specfact_code_review/tools/test_pylint_runner.py'
E   ModuleNotFoundError: No module named 'specfact_code_review.tools.pylint_runner'
```

## Passing test evidence

Command:

```bash
hatch run python -m pytest tests/unit/specfact_code_review/tools/test_basedpyright_runner.py tests/unit/specfact_code_review/tools/test_pylint_runner.py -v
```

Observed pass:

```text
tests/unit/specfact_code_review/tools/test_basedpyright_runner.py::test_run_basedpyright_maps_error_diagnostic_to_type_safety PASSED
tests/unit/specfact_code_review/tools/test_basedpyright_runner.py::test_run_basedpyright_maps_warning_severity PASSED
tests/unit/specfact_code_review/tools/test_basedpyright_runner.py::test_run_basedpyright_filters_findings_to_requested_files PASSED
tests/unit/specfact_code_review/tools/test_basedpyright_runner.py::test_run_basedpyright_returns_tool_error_when_unavailable PASSED
tests/unit/specfact_code_review/tools/test_pylint_runner.py::test_run_pylint_maps_bare_except_to_architecture PASSED
tests/unit/specfact_code_review/tools/test_pylint_runner.py::test_run_pylint_maps_broad_except_to_architecture PASSED
tests/unit/specfact_code_review/tools/test_pylint_runner.py::test_run_pylint_filters_findings_to_requested_files PASSED
tests/unit/specfact_code_review/tools/test_pylint_runner.py::test_run_pylint_returns_tool_error_on_parse_error PASSED

============================== 8 passed in 0.41s ===============================
```
