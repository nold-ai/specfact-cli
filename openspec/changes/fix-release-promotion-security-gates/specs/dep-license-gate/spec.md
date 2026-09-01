## ADDED Requirements

### Requirement: Frozen development advisories use a compatible fixed graph

When an optional development tool pins a vulnerable transitive package and a
compatible released tool version pins a fixed package, the repository SHALL
upgrade the tool and transitive package together in every authoritative frozen
representation and SHALL remove the obsolete advisory exception.

#### Scenario: Semgrep selects a fixed MCP line

- **GIVEN** Semgrep 1.171.0 resolves vulnerable `mcp==1.23.3`
- **AND** released Semgrep 1.175.0 declares compatible `mcp==1.29.0`
- **WHEN** the security patch refreshes the frozen graph
- **THEN** `uv.lock` and `requirements/ci/locked.txt` SHALL contain Semgrep 1.175.0 and MCP 1.29.0
- **AND** policy SHALL enforce Semgrep 1.175.0 and MCP 1.28.1 minimums
- **AND** no MCP advisory waiver SHALL remain
- **AND** neither package SHALL become a core runtime dependency.

### Requirement: License exceptions are bound to an exact environment scope

An exception documented for the isolated hash-locked Code Review interpreter
SHALL apply only to that interpreter. The primary environment, generic
additional interpreters, and module manifests SHALL remain ineligible.

#### Scenario: Code Review-only Pylint exception cannot suppress primary violations

- **GIVEN** the allowlist marks the exact Pylint version as `code-review-only`
- **WHEN** the license gate scans the primary or a generic additional interpreter
- **THEN** it SHALL reject the GPL Pylint record
- **AND** the exact frozen Code Review interpreter MAY accept only the matching version and license.

### Requirement: Isolated Code Review locks are dependency-trust inputs

The dependency-trust gate SHALL authenticate the Code Review requirements input
and hash-locked export, require exact pins with attached hashes, and apply the
same blocked-package and minimum-version policy before installation.

#### Scenario: Modified or weak Code Review lock fails closed

- **WHEN** the Code Review input digest changes, a package is not exactly pinned,
  a pin has no attached hash, or a package violates the security policy
- **THEN** dependency-trust validation SHALL fail before the isolated environment is installed.

### Requirement: Patch release consumes only the next version

This bugfix SHALL advance every canonical package version source from 0.55.3 to
0.55.4 without changing the core runtime dependency membership.

#### Scenario: Canonical version sources remain synchronized

- **WHEN** the security patch is prepared for release
- **THEN** `pyproject.toml`, `setup.py`, `src/__init__.py`, and
  `src/specfact_cli/__init__.py` SHALL all declare 0.55.4
- **AND** no later minor or patch version SHALL be consumed by this change.
