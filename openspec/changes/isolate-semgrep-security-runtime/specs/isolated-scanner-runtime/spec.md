## ADDED Requirements

### Requirement: Exclude compromised certificate authorities from delivered trust

The supported frozen Python closure SHALL use a certifi bundle that excludes the
compromised emSign ECC Root CA - G3 certificate, identified by DER SHA256
`86a1ecba089c4a8d3bbe2734c612ba341d813e043cf9e8a862cd5c57a36bbe6b`.
The bundle SHALL retain a nonempty set of trusted certificates. Canonical
requirements and generated locked exports SHALL require certifi >=2026.10.19.
Every existing dependency audit and trust gate SHALL remain enforced; this patch
SHALL NOT claim remediation of the distinct MCP advisory or native scanner work.

#### Scenario: Installed certificate bundle rejects the compromised root

- **GIVEN** the certificate bundle installed by the exact frozen Python inputs
- **WHEN** a TLS context loads certifi's CA file and enumerates trusted DER certificates
- **THEN** the trust store is nonempty and does not contain the compromised root's SHA256.
