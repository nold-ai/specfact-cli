# TDD evidence

## Failing before the fix

- `hatch run pytest -q tests/unit/cli/test_typer_compatibility.py` on Python 3.12.13 with Typer 0.29.3 failed importing core. The error was `AttributeError: module 'typer.main' has no attribute 'get_params_convertors_ctx_param_name_from_function'`.
- An isolated Python 3.13 uvx installation of the unmodified 0.55.19 wheel failed with the same error before `--version` ran.
- On Typer 0.29.3, both Typer cases in `test_generator_preserves_positional_argument_contract` failed because direct construction of `TyperArgument` now requires `type_descriptor`. The Click cases passed.
- After switching that fixture to real Typer commands, the optional positional argument still failed because Typer 0.29.3 no longer exposes `human_readable_name`. The required argument with an explicit metavar passed.

## Passing after the fix

- On 27 November 2026, the CLI, docs parity, and official module command tests passed with Typer 0.29.3 and 0.27.0. The reviewed module source fixture was `69f07581` and the approved archive fixture was `046d366c`. The command audit also passed with the current modules release source at `209b4ed8`.
- The rebuilt 0.55.19 wheel resolved Typer 0.29.3 on Python 3.13 from a new uv cache without a dependency override. Default startup, `--version`, `module list --show-origin`, `project --help`, and `spec --help` exited successfully.
- Isolated uvx startup checks also passed on Python 3.11 and 3.12. The combined regression suite passed 128 tests with one skip on each of Typer 0.29.3 and 0.27.0.
- Repository Ruff, error-level BasedPyright, and strict OpenSpec validation passed. `uv lock --check` confirmed that the frozen inputs still resolve.

## Delivery gate status

- The local full smart-test run remained red. It started before the final documentation fixture repair and also reported a missing Hatchling build backend and failures in the local Requirements fixtures. The final focused suite covered the repaired documentation cases.
- The SpecFact Code Review capsule reported `unsupported_controller_platform` on macOS. Independent Python SAST passed with zero new findings. Bandit reported zero medium or high findings.
