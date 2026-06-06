# dep-license-gate Specification

## Purpose
TBD - created by archiving change dep-security-cleanup. Update Purpose after archive.
## Requirements
### Requirement: Automated license compliance gate

The system SHALL provide a `hatch run license-check` script that scans all installed packages in the active environment and fails if any package carries a GPL-2.0, GPL-3.0, AGPL-3.0, GPL-2.0-or-later, GPL-3.0-or-later, or AGPL-3.0-or-later license that is not present in the project's documented exception allowlist. This gate SHALL be executable in CI and locally.

The gate SHALL be implemented as `scripts/check_license_compliance.py` using `pip-licenses` to enumerate installed packages and their SPDX expressions.

#### Scenario: All packages are license-compliant

- **WHEN** `hatch run license-check` is executed
- **AND** no installed package has a GPL or AGPL license outside the allowlist
- **THEN** the script SHALL exit with code 0
- **AND** SHALL print a summary of all packages and their licenses

#### Scenario: GPL package detected outside allowlist

- **WHEN** `hatch run license-check` is executed
- **AND** an installed package carries a GPL or AGPL license not in the exception allowlist
- **THEN** the script SHALL exit with code 1
- **AND** SHALL print the offending package name, version, and license
- **AND** SHALL print the message: `LICENSE VIOLATION: <package>==<version> uses <license> which is incompatible with Apache-2.0`

#### Scenario: Package in exception allowlist is accepted

- **WHEN** `hatch run license-check` is executed
- **AND** an installed package is in the allowlist (e.g., `pygments`, `pylint`, `semgrep`)
- **THEN** the script SHALL accept the package without failing
- **AND** SHALL print: `EXCEPTION: <package>==<version> (<license>) — <reason>`

#### Scenario: Unknown license triggers warning, not failure

- **WHEN** `hatch run license-check` is executed
- **AND** a package has no SPDX expression or `UNKNOWN` license
- **THEN** the script SHALL print a WARNING for each such package
- **AND** SHALL NOT fail the gate (these are investigated separately)
- **AND** SHALL include the warning in the summary output

### Requirement: License exception allowlist file

The project SHALL maintain a `scripts/license_allowlist.yaml` file that documents all accepted GPL/LGPL exception packages. Each entry SHALL include the package name, accepted license, and a human-readable reason.

#### Scenario: Allowlist file exists and is parseable

- **WHEN** `scripts/check_license_compliance.py` runs
- **THEN** it SHALL load `scripts/license_allowlist.yaml`
- **AND** each entry SHALL have `package`, `license`, and `reason` fields
- **AND** the script SHALL fail with a clear error if the allowlist file is missing or malformed

#### Scenario: Manifest dependency missing from static license map

- **WHEN** `hatch run license-check` evaluates `pip_dependencies` in a `module-package.yaml`
- **AND** the dependency name is not listed under `licenses` in `scripts/module_pip_dependencies_licenses.yaml`
- **THEN** the gate SHALL exit with code 1
- **AND** SHALL print a `MODULE MANIFEST VIOLATION` message that names the dependency and the mapping file

#### Scenario: New (A)GPL package added to pyproject.toml without allowlist entry

- **WHEN** a developer adds a new GPL or AGPL package to any extra in `pyproject.toml`
- **AND** runs `hatch run license-check`
- **THEN** the gate SHALL fail
- **AND** SHALL instruct the developer to either remove the package or add an allowlist entry with a documented reason

### Requirement: Automated CVE and security audit gate

The system SHALL provide a `hatch run security-audit` script that runs `pip-audit` against the active environment to detect known CVEs in installed packages. The gate SHALL fail if any vulnerability with CVSS score >= 7.0 (high severity) is found.

`pip-audit` (MIT, by Python Packaging Authority) is the standard CVE scanning tool for Python packages, backed by the OSV and PyPI vulnerability databases.

#### Scenario: No CVEs found

- **WHEN** `hatch run security-audit` is executed
- **AND** no installed package has a known CVE at high severity
- **THEN** the script SHALL exit with code 0
- **AND** SHALL print: `Security audit passed. No high-severity vulnerabilities found.`

#### Scenario: High-severity CVE found

- **WHEN** `hatch run security-audit` is executed
- **AND** an installed package has a CVE with CVSS >= 7.0
- **THEN** the script SHALL exit with code 1
- **AND** SHALL print the package name, version, CVE ID, CVSS score, and description
- **AND** SHALL print: `ACTION REQUIRED: Update or replace <package>==<version>`

#### Scenario: Low/medium CVE found — warning only

- **WHEN** `hatch run security-audit` is executed
- **AND** an installed package has a CVE with CVSS < 7.0
- **THEN** the script SHALL print a WARNING with the details
- **AND** SHALL NOT fail the gate (engineer reviews and decides)

#### Scenario: pip-audit not available

- **WHEN** `hatch run security-audit` is executed
- **AND** `pip-audit` is not installed
- **THEN** the script SHALL print an error: `pip-audit not installed. Run: pip install pip-audit`
- **AND** SHALL exit with code 1

### Requirement: CI integration for license and security gates

The license compliance gate SHALL be integrated into the project's CI workflow
as a separate step that runs on pull requests modifying dependency manifests
such as `pyproject.toml`. The security audit gate SHALL run on every PR. The
agent-rules documentation SHALL reference these gates as mandatory checks before
merging any dependency change.

#### Scenario: License gate runs in CI on dependency changes

- **WHEN** a pull request modifies `pyproject.toml` **and** matches the PR orchestrator's non-documentation code-change filter
- **THEN** the CI workflow SHALL run the license compliance gate (`hatch run license-check` / `scripts/check_license_compliance.py`)
- **AND** SHALL block merge if the gate fails

#### Scenario: Security audit runs in CI on all PRs

- **WHEN** any pull request is opened or updated
- **THEN** the CI workflow SHALL run `hatch run security-audit`
- **AND** SHALL block merge if any high-severity CVE is found

### Requirement: Agent-rules documentation for dependency hygiene

The project's `docs/agent-rules/` framework SHALL include a dedicated section on dependency hygiene that specifies:

- No packages without a known SPDX license expression (treat as unknown risk)
- All new runtime dependencies must have MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, or PSF licenses
- `hatch run license-check` and `hatch run security-audit` are required before any dependency change is merged

#### Scenario: Agent reads dependency hygiene rules

- **WHEN** an AI agent or developer reviews the agent-rules framework
- **THEN** `docs/agent-rules/` SHALL contain explicit rules about (A)GPL prohibition, allowlist process, and required gate scripts
- **AND** these rules SHALL be discoverable via the INDEX.md

#### Scenario: Developer adds dependency without license check

- **WHEN** a PR adds a new package to pyproject.toml
- **AND** the license-check gate is not run
- **THEN** CI SHALL catch the omission and require the gate to pass before merge
