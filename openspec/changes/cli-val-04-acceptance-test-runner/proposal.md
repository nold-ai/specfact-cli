# Change: Acceptance Test Runner

## Why

The 73+ existing CliRunner tests prove commands work in-process. But SpecFact is distributed as a pip-installable binary (`specfact` and `specfact-cli` entry points). Nothing currently proves the installed binary works — entry point resolution, environment variable handling, exit code propagation to shell, real stdout/stderr separation. A packaging bug could ship a CLI that passes all tests but fails on `pip install specfact-cli && specfact --help`. A dual-path test runner that executes CLI behavior scenarios both in-process (fast) and as a real subprocess (true black-box) closes this gap.

## What Changes

- **NEW**: Dual-path scenario runner in `tools/cli_acceptance_runner.py` that reads YAML scenarios from cli-val-01 and executes them via:
  - Fast path: `typer.testing.CliRunner` (for development speed)
  - Black-box path: `subprocess.run()` against a built-wheel installation of the `specfact` and `specfact-cli` binaries (for CI/release validation)
- **NEW**: Acceptance test file `tests/e2e/test_cli_acceptance.py` wiring the runner into pytest collection
- **NEW**: Small set of Cram-style `.t` or Markdown acceptance tests for 3-5 flagship command chains (living documentation + executable tests)
- **EXTEND**: `pyproject.toml` with hatch scripts for fast-path and black-box acceptance runs

## Capabilities

### New Capabilities

- `acceptance-test-runner`: A dual-path test runner that executes CLI behavior scenarios from YAML files via CliRunner (fast, in-process) or subprocess (black-box, against a built-wheel installed binary). Supports workspace setup, exit code assertions, output pattern matching, and filesystem diff verification.

## Impact

- **Affected specs**: No existing specs modified; new spec delta defines runner behavior
- **Affected code**: New tools/ and tests/ files only; no production CLI code changes
- **Integration points**: Consumes cli-val-01 YAML scenarios and cli-val-03 anti-patterns; consumed by cli-val-05 (CI gate builds a wheel and runs the black-box path)
- **Documentation impact**: Developer guide update describing acceptance test workflow and how to add new scenarios

## Dependencies

- **Hard blocker**: cli-val-01-behavior-contract-standard (YAML scenario format)
- **Hard blocker**: cli-val-03-misuse-safety-proof (anti-patterns run through the runner)
- Downstream dependents: cli-val-05-ci-integration

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #282
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/282>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
