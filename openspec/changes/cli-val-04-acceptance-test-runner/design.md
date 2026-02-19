## Context

This change implements the runner that compiles CLI behavior scenarios (from cli-val-01) and anti-patterns (from cli-val-03) into executable tests, supporting both fast in-process and true black-box execution paths.

## Goals / Non-Goals

**Goals:**

- Implement a dual-path runner (CliRunner + subprocess.run) that reads YAML scenarios
- Integrate with pytest collection for standard test reporting
- Support workspace setup, output assertions, and filesystem diff verification
- Create flagship command chain acceptance tests for key workflows
- Add hatch scripts for both execution paths

**Non-Goals:**

- No CI gating (that is cli-val-05)
- No scenario file authoring (that is cli-val-01 + cli-val-03)
- No interactive prompt testing (pexpect integration is future scope)
- No Cram/Prysk/Scrut integration in this iteration (evaluate after initial runner proves value)

## Decisions

- Runner is a tool (`tools/cli_acceptance_runner.py`) rather than a pytest plugin — keeps it simple and reusable
- Subprocess path uses `subprocess.run()` with `capture_output=True` and `text=True` — standard Python, no external dependencies
- Workspace context setup uses a factory pattern: `empty-repo`, `sample-bundle`, `initialized-project` are predefined fixtures
- Black-box tests use a `@pytest.mark.blackbox` marker for selective execution in CI
- Flagship command chain tests are hand-written in `tests/e2e/` rather than YAML-driven — captures workflow sequencing that YAML scenarios cannot express

## Risks / Trade-offs

- [subprocess tests depend on installed binary] -> Mitigation: CI installs via `pip install -e .` before running black-box tests
- [Subprocess tests are slower] -> Mitigation: mark as `blackbox` for selective execution; fast path covers most validation
- [Context setup complexity] -> Mitigation: start with 3 simple context types; extend as needed

## Migration Plan

1. Implement scenario loader and dual-path runner
2. Create pytest integration test file
3. Wire hatch scripts for fast and black-box paths
4. Create 3-5 flagship command chain tests
5. Verify both paths produce consistent results

## Open Questions

- Whether to adopt Cram/Prysk/Scrut for the flagship tests in a future iteration
- Whether the black-box path should test the `specfact` or `specfact-cli` entry point (or both)
