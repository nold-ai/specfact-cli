# package-distribution Specification

## Purpose
TBD - created by archiving change packaging-01-wheel-package-inclusion. Update Purpose after archive.
## Requirements
### Requirement: Released wheel includes core CLI package

The published wheel MUST include the importable `specfact_cli` Python package required by declared console scripts.

#### Scenario: Wheel contains core CLI module
- **GIVEN** a wheel is built from the repository release configuration
- **WHEN** its contents are inspected
- **THEN** it includes `specfact_cli/cli.py`
- **AND** it includes `specfact_cli/__init__.py`

#### Scenario: Console scripts target importable CLI entrypoint
- **GIVEN** the built distribution metadata
- **WHEN** console script entrypoints are inspected
- **THEN** both `specfact` and `specfact-cli` resolve to `specfact_cli.cli:cli_main`
- **AND** importing `specfact_cli.cli` from the built artifact succeeds

