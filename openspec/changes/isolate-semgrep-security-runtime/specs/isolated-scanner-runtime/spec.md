## ADDED Requirements

### Requirement: Exclude compromised certificate authorities from delivered trust

The exact frozen certifi wheel and installed runtime SHALL exclude compromised
emSign ECC Root CA - G3 DER SHA256
`86a1ecba089c4a8d3bbe2734c612ba341d813e043cf9e8a862cd5c57a36bbe6b`
while retaining a nonempty CA store. Canonical inputs SHALL require certifi
>=2026.10.19. Trusted Requirements proof SHALL bind the candidate tree's wheel
bytes to its frozen SHA256 and inspect inert CA data without importing candidate
dependencies into the trusted verifier. Every existing audit remains enforced.

#### Scenario: Frozen certificate artifact rejects the compromised root

- **GIVEN** the exact certifi wheel selected by the candidate lock and hash export
- **WHEN** its verified CA data is parsed as a trusted SSL context
- **THEN** the store is nonempty and excludes the compromised DER fingerprint, independently of the verifier's installed certifi.

### Requirement: Produce MCP-patched Semgrep wheels without changing scanner payloads

The bounded producer SHALL transform the seven exact reviewed Semgrep 1.179.0
wheels into proposed `specfact-semgrep==1.179.0.post1` wheels requiring MCP 1.30.0.
Only explicitly reviewed distribution metadata, identity-derived archive roots
and RECORD SHALL change. All other bytes, modes, complete tags, entrypoints and
notices SHALL remain. Source/hash/archive/metadata drift SHALL fail closed.
Canonical CI SHALL build each artifact once, test those same bytes in all 21
supported native Python/platform cells, and attest exact source and evidence.
Candidate success SHALL NOT imply publication, consumer adoption or audit success.

#### Scenario: Selected scanner artifact declares patched MCP and unchanged payloads

- **GIVEN** the exact current upstream scanner wheel, or the output of the repository producer when implemented
- **WHEN** its metadata and payload inventory are inspected without executing it
- **THEN** it declares MCP 1.30.0 and the legal downstream identity while retaining every other payload byte, mode, full tag, entrypoint and notice.
