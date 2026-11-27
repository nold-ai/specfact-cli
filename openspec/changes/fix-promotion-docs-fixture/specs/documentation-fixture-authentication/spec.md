## ADDED Requirements

### Requirement: Promotion checks authenticate the reviewed documentation source

Docs Review and CLI Command Validation SHALL check the official immutable fixture identity and exact package digest against the protected base lock before exposing reviewed documentation module sources. Fixtures outside that identity SHALL still pass strict publisher signature and filesystem verification using the protected base verifier.

#### Scenario: The reviewed fixture survives the key rotation

- **WHEN** the official fixture checkout and all package files match the identity and digest in the protected base lock
- **THEN** both jobs expose the reviewed source for command validation

#### Scenario: Altered or unapproved source stays rejected

- **WHEN** the checkout matches the protected identity but the packages differ, or an unsigned fixture supplies its own lock
- **THEN** both jobs fail before exposing the source
