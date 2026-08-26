# dep-license-gate Specification

## Purpose

Define the repository's license-compliance and frozen-advisory gates so CI and local
contributors reject unapproved (A)GPL dependencies and unreviewed vulnerabilities.

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

The system SHALL provide a `hatch run security-audit` script that runs
`pip-audit --strict` against the committed hash-protected requirements export,
not an ambient environment. The gate SHALL fail on every unreviewed known
advisory; CVSS metadata is reported but SHALL NOT downgrade a finding to a
warning-only result. When a compatible fixed release exists for a validated
finding, the repository SHALL select that fixed line and regenerate every
authoritative frozen dependency representation together instead of adding an
exception.

`pip-audit` (MIT, by Python Packaging Authority) is the standard CVE scanning tool
for Python packages, backed by the OSV and PyPI vulnerability databases.

#### Scenario: No unreviewed CVEs found

- **WHEN** `hatch run security-audit` is executed
- **AND** no frozen package has an unreviewed known advisory
- **THEN** the script SHALL exit with code 0
- **AND** SHALL print: `Security audit passed. No unreviewed vulnerabilities found in the frozen requirements.`

#### Scenario: Any unreviewed CVE found

- **WHEN** `hatch run security-audit` is executed
- **AND** a frozen package has a known advisory without a matching, unexpired exception
- **THEN** the script SHALL exit with code 1
- **AND** SHALL print the package name, version, CVE ID, CVSS score, and description
- **AND** SHALL print an `ACTION REQUIRED` remediation message.

#### Scenario: Compatible fixed dependency release exists

- **GIVEN** the committed frozen graph contains a package version affected by a validated advisory
- **AND** a compatible fixed release is available
- **WHEN** the advisory is remediated
- **THEN** the direct constraints, `uv.lock`, and `requirements/ci/locked.txt` SHALL resolve to the fixed line together
- **AND** the repository SHALL NOT add a temporary exception for that finding
- **AND** the reproducible-delivery checker and security audit SHALL pass against the same committed graph.

#### Scenario: Patched tooling floor does not expand runtime dependencies

- **GIVEN** pip is required transitively by development audit and resolver tools
- **WHEN** the repository declares the minimum patched pip version
- **THEN** both the development extra and default Hatch environment SHALL require `pip>=26.2`
- **AND** both tooling surfaces SHALL require `pip-tools>=7.6.1`
- **AND** core project dependencies and `setup.py` SHALL remain pip-free.

#### Scenario: Updated build backend remains publishable

- **GIVEN** the compatible Hatchling update defaults to Core Metadata 2.5
- **AND** Twine 7.0 or newer accepts that metadata version
- **WHEN** the repository builds the patch-release wheel
- **THEN** the development tooling SHALL require `twine>=7.0`
- **AND** the wheel SHALL retain the build backend's current metadata format
- **AND** the frozen Twine validation SHALL accept the built wheel.

#### Scenario: Exact temporary advisory exception

- **WHEN** `hatch run security-audit` is executed
- **AND** a reviewed exception matches the exact package, version, and advisory ID
- **THEN** the script SHALL allow only that finding while printing a `WAIVED` record
- **AND** SHALL fail when the exception lacks mitigation/rationale or is expired.

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
- **AND** SHALL block merge if any unreviewed advisory is found

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
