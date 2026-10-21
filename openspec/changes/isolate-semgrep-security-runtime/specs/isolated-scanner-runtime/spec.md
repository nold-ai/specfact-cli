## ADDED Requirements

### Requirement: Exclude compromised certificate authorities from delivered trust

The exact frozen certifi wheel SHALL exclude compromised
emSign ECC Root CA - G3 DER SHA256
`86a1ecba089c4a8d3bbe2734c612ba341d813e043cf9e8a862cd5c57a36bbe6b`
while retaining a nonempty CA store. Canonical inputs SHALL require certifi
>=2026.10.19. Trusted Requirements proof SHALL inspect hash-bound inert CA data
without importing candidate dependencies into its verifier.

#### Scenario: Frozen certificate artifact rejects the compromised root

- **GIVEN** the certifi wheel selected by the frozen lock and hash export
- **WHEN** verified CA data is parsed by trusted SSL code
- **THEN** the store is nonempty and excludes the compromised DER fingerprint.

### Requirement: Bound the temporary official MCP advisory exception

The unchanged official Semgrep/MCP graph SHALL use only an exact reviewed
MCP 1.29.0 / CVE-2026-59951 exception, including its GHSA alias, from 2026-10-21
through 2026-11-04 inclusive. Every required audit SHALL remain strict and fail
closed on other versions, advisories, skipped dependencies, malformed records
or expiry. No Semgrep fork or conflicting dependency override SHALL be adopted.

#### Scenario: Only the approved official MCP finding is waived

- **GIVEN** the reviewed MCP register record and the official frozen graph
- **WHEN** the existing audit gate evaluates it on the review date
- **THEN** only the exact authorized finding passes with a visible WAIVED report.

#### Scenario: An unrelated or expired finding remains blocking

- **GIVEN** the reviewed record with a different version, advisory, skipped subject or date after expiry
- **WHEN** the existing audit gate evaluates that input
- **THEN** it returns a failure instead of suppressing the finding.
