## ADDED Requirements

### Requirement: Select reviewed official patch versions

The frozen graph and CI export SHALL select official GitPython 3.2.1,
packaging 26.3, pycparser 3.12, python-discovery 1.6.1, virtualenv 21.14.13,
filelock 4.2.1, msgpack 1.2.3, setuptools 84.1.0 and Semgrep 1.182.1.
Every selected artifact SHALL remain hash-bound to the official registry.

#### Scenario: Each missing package update reaches frozen delivery

- **GIVEN** the reviewed package/version table
- **WHEN** the lock and CI export are inspected
- **THEN** each contains exactly the reviewed official version and equal
  nonempty SHA-256 artifact sets; missing or substituted export hashes fail.

### Requirement: Declare the corrected public dependency floors

Both public dependency declarations SHALL require GitPython >=3.2.1 and
pycparser >=3.12,!=3.0.* while preserving all unrelated requirements.

#### Scenario: Both declarations reject the superseded vulnerable selections

- **GIVEN** pyproject.toml and setup.py
- **WHEN** their dependency requirements are read
- **THEN** both expose the corrected GitPython and parser floors.

### Requirement: Replace expired parser provenance with exact reviewed bytes

The parser review SHALL bind official pycparser 3.12 wheel SHA-256
`a076f3f489b39b43ed13563a1dafe42447445bec2e294154ec5c57fcdda4c85e`,
reviewed 22 October 2026 UTC and expiring 4 November 2026 inclusive. The
expired 2.22 review SHALL NOT be renewed. Blocked 3.0 aliases, mismatched
artifacts and dates outside the review window SHALL remain refused.

#### Scenario: Bootstrap validates the reviewed parser record

- **GIVEN** the exact committed parser record and matching frozen artifacts
- **WHEN** the standard-library trust checker evaluates them
- **THEN** it accepts only the reviewed version, source, digest and dates.

### Requirement: Bound the separately approved OpenTelemetry exception

The existing strict audit gate MAY admit only OpenTelemetry API 1.37.0
CVE-2026-114603 or its GHSA-xcq7-p3pf-p88h alias from 22 October through
4 November 2026 inclusive, under the separately approved mitigation. Ordinary
local-rule CLI scanning SHALL NOT expose an instrumented HTTP service to
untrusted propagation headers. The MCP record SHALL remain separate. Other
packages, versions, advisories, skipped subjects and invalid dates SHALL fail.

#### Scenario: Exact OpenTelemetry finding passes within the approval window

- **GIVEN** the distinct committed OpenTelemetry record
- **WHEN** the audit gate sees either exact advisory ID on an authorized date
- **THEN** only that finding is visibly admitted and other checks remain strict.

### Requirement: Reject submodule creation inside Git metadata

The frozen GitPython API SHALL reject `.git/hooks`, `GIT~1/hooks` and absolute
metadata paths before cloning or modifying Git metadata. Ordinary `vendor`
and `.github` checkouts SHALL still reach the clone boundary.

#### Scenario: Metadata checkout refuses before side effects

- **GIVEN** the exact frozen GitPython and its hash-pinned dependency closure
- **WHEN** create_submodule receives a metadata checkout path
- **THEN** it raises ValueError before cloning, leaves hooks unchanged and
  creates neither .gitmodules nor submodule metadata.

### Requirement: Keep frozen assertions out of advisory resolver lanes

The scheduled advisory latest/lower-bound resolver lanes SHALL add exactly
the seven reviewed frozen-release deselections to their two existing file
exclusions. Both lanes SHALL use identical selection, retaining every other
ordinary case in the exercised test files. Blocking jobs SHALL retain their
complete frozen test selection.

#### Scenario: Both advisory resolutions preserve the intended selection

- **GIVEN** both scheduled resolver commands and the actual test inventory
- **WHEN** their selected cases are collected
- **THEN** both use exactly the two existing file exclusions and seven added
  selectors, retain all other cases in the exercised files and leave every
  blocking job unchanged.

### Requirement: Preserve strict audits with exact bounded residual risk

All three strict frozen audits SHALL remain enforced, including setuptools
84.1.0 in the affected graphs and Pylint 4.0.9 in the isolated Code Review
input and hash-bound lock. Only the exact reviewed package, version and
advisory identities MAY be admitted within their existing dates. The original
MCP 1.29.0 record and the separate OpenTelemetry 1.37.0 record SHALL remain
separate from the MCP 1.29.0 record reviewed on 29 October 2026 for
CVE-2026-116685 / GHSA-5h93-6whr-6q8j, CVE-2026-116686 /
GHSA-rwrf-2pqf-9j8j and CVE-2026-116684 / GHSA-w4fh-qvv9-3v23.
All records SHALL expire on 4 November 2026 inclusive. This is accepted
residual risk while the official Semgrep 1.182.1 pin remains incompatible
with patched MCP, not remediation or a general waiver. The documented CLI-only
mitigations SHALL remain in force.

#### Scenario: Unreviewed or expired findings remain blocking

- **GIVEN** the three strict audit reports and the exact three review records
- **WHEN** a finding has another package, version or advisory, or the record
  is expired, or an audit subject is skipped
- **THEN** the audit fails without widening an exception or omitting a subject.
