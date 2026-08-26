## MODIFIED Requirements

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
