# upgrade-command Specification

## Purpose

TBD - created by archiving change upgrade-01-install-method-aware. Update Purpose after archive.

## Requirements

### Requirement: Upgrade command must respect installation method

`specfact upgrade` SHALL detect whether SpecFact is installed via pip, pipx, uv, or uvx and present/execute an installation-method-appropriate upgrade command.

#### Scenario: uv-managed environment

- **WHEN** SpecFact runs from a uv-managed virtual environment or uv executable context
- **THEN** detection returns `uv`
- **AND** update command uses uv-native upgrade invocation.
