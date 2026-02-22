# TDD Evidence: validation-01-deep-validation

## Behavior change: CrossHair per-path timeout option

### Pre-implementation (failing test)

- **Test**: `tests/unit/validators/test_repro_checker.py::TestReproChecker::test_repro_checker_crosshair_per_path_timeout_passed_to_command`
- **Command**: `hatch test -- tests/unit/validators/test_repro_checker.py -v -k "crosshair_per_path"`
- **Timestamp**: 2026-02-18 (before implementation)
- **Result**: Failed — `ReproChecker` had no `crosshair_per_path_timeout` and CrossHair command did not include `--per_path_timeout`.

### Post-implementation (passing test)

- **Command**: `hatch test -- tests/unit/validators/test_repro_checker.py -v -k "crosshair_per_path"`
- **Timestamp**: 2026-02-18
- **Result**: Passed — `ReproChecker(repo_path=..., crosshair_per_path_timeout=60)` produces a CrossHair invocation with `--per_path_timeout` and `60` in the command list.

### Implementation summary

1. Added `crosshair_per_path_timeout: int | None = None` to `ReproChecker.__init__` and stored on `self`.
2. In `run_all_checks()`, when building `crosshair_base`, append `--per_path_timeout` and the value when `self.crosshair_per_path_timeout` is set and > 0.
3. Added `--crosshair-per-path-timeout` option to repro command in `src/specfact_cli/modules/repro/src/commands.py` and passed through to `ReproChecker`.
4. Unit test mocks `subprocess.run` at `specfact_cli.validators.repro_checker.subprocess.run`, runs `run_all_checks()` with `crosshair_per_path_timeout=60`, and asserts the CrossHair call includes `--per_path_timeout` and `60`.
