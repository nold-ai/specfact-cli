# Change Validation

## Scope check

This change is narrowly scoped to Python package distribution for `pip install specfact-cli`.

## Implemented

- Switched Hatch wheel target from shorthand `packages = ["src/specfact_cli"]` to explicit:
  - `only-include = ["src/specfact_cli"]`
  - `sources = ["src"]`
- Added regression coverage for explicit wheel source mapping and console script entrypoints.
- Verified built wheel contents include `specfact_cli/__init__.py` and `specfact_cli/cli.py`.

## Validation summary

- packaging regression tests: pass
- built wheel artifact inspection: pass
- direct import from built wheel: pass

## Release note

A patch release is required before PyPI users receive this fix, because `0.40.0` is already published with the broken wheel payload.

## Install verification

A clean temp venv install of `dist/specfact_cli-0.40.1-py3-none-any.whl` was verified with both:
- `specfact -v`
- `specfact-cli -v`

Both commands returned `SpecFact CLI version 0.40.1`.
