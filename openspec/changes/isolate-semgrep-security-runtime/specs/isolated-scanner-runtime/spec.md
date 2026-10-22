## ADDED Requirements

### Requirement: Exclude compromised certificate authorities from delivered trust

The main release SHALL satisfy this delivery contract using the reviewed official dependencies.

#### Scenario: Exclude compromised certificate authorities from delivered trust

- **WHEN** the exact frozen certifi wheel is inspected and its CA certificates are parsed
- **THEN** the trust store SHALL be nonempty and exclude emSign ECC Root CA - G3 DER SHA256 86a1ecba089c4a8d3bbe2734c612ba341d813e043cf9e8a862cd5c57a36bbe6b
- **AND** malformed artifacts, invalid hashes, and unapproved origins SHALL be rejected.

### Requirement: Reject submodule checkouts outside the repository

The main release SHALL satisfy this delivery contract using the reviewed official dependencies.

#### Scenario: Reject submodule checkouts outside the repository

- **WHEN** the exact frozen GitPython wheel updates a submodule with path ../outside
- **THEN** it SHALL reject the path before invoking clone and SHALL create no outside directory.

### Requirement: Preserve JWT verification options and compatibility

The main release SHALL satisfy this delivery contract using the reviewed official dependencies.

#### Scenario: Preserve JWT verification options and compatibility

- **WHEN** the exact frozen PyJWT wheel inspects a token without signature verification and caller options are reused for verified decoding
- **THEN** inspection SHALL preserve caller options and expiry verification SHALL still reject an expired token
- **AND** signed decoding and supported signature padding SHALL remain compatible.

### Requirement: Select the reviewed compatible tooling graph

The main release SHALL satisfy this delivery contract using the reviewed official dependencies.

#### Scenario: Select the reviewed compatible tooling graph

- **WHEN** the release frozen graph is resolved
- **THEN** it SHALL select certifi 2026.10.19, GitPython 3.2.0, PyJWT 2.15.1, Hatchling 1.32.4, urllib3 2.8.0, virtualenv 21.14.12, python-discovery 1.6.1, and packaging 26.3
- **AND** the lock and hashed delivery export SHALL agree.

### Requirement: Bound the temporary official MCP advisory exception

The main release SHALL satisfy this delivery contract using the reviewed official dependencies.

#### Scenario: Bound the temporary official MCP advisory exception

- **WHEN** official Semgrep 1.179.0 selects MCP 1.29.0
- **THEN** only CVE-2026-59951 and its alias GHSA-84m7-p3x7-pcfv SHALL be waived from 2026-10-21 through 2026-11-04 inclusive
- **AND** other versions, unrelated or mixed advisories, skipped dependencies, expired records, and future review dates SHALL fail closed.

### Requirement: Rebuild the source distribution with its bundled manifest

The main release SHALL satisfy this delivery contract using the reviewed official dependencies.

#### Scenario: Rebuild the source distribution with its bundled manifest

- **WHEN** the ordinary offline PEP 517 source-distribution-to-wheel build runs
- **THEN** the build SHALL succeed and the wheel SHALL contain the original bundle-mapper manifest bytes.

### Requirement: Select the reviewed documentation dependency versions

The main release SHALL satisfy this delivery contract using the reviewed official dependencies.

#### Scenario: Select the reviewed documentation dependency versions

- **WHEN** the documentation dependencies are installed from the lock
- **THEN** jekyll-feed 0.18.0, jekyll-redirect-from 0.17.0, and jekyll-relative-links 0.9.1 SHALL be selected
- **AND** JSON SHALL be constrained to >=2.21.2,<3

### Requirement: Publish one coherent patch version

The main release SHALL satisfy this delivery contract using the reviewed official dependencies.

#### Scenario: Publish one coherent patch version

- **WHEN** release metadata is read
- **THEN** all four canonical version sources SHALL declare 0.55.11.
