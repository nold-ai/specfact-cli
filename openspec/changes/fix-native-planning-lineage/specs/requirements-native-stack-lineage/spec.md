## ADDED Requirements

### Requirement: Preserve native planning parent lineage

Independent execution SHALL distinguish protected verifier trust from authenticated planning selection.
The protected proof base SHALL be an ancestor of the immutable review merge base. The planning/evidence
base SHALL be an ancestor of the candidate source. Both commit identities SHALL be valid. Native review
projection SHALL NOT replace authenticated planning selection or protected validator authority.

#### Scenario: Planning parent is newer than the protected review base

- **GIVEN** authenticated protected dev, a verified security parent and an eligible planning child
- **WHEN** native CI exposes dev as the review base
- **THEN** independent execution SHALL admit valid planning ancestry before ordinary reconciliation
- **AND** ordinary protected-base validation SHALL remain available
- **AND** plan/context equality and inherited proof/authority authentication SHALL remain required

### Requirement: Reject independent lineage forgery

Independent execution SHALL reject unrelated protected trust, unrelated planning ancestry or evidence
newer than the candidate. Planning selection SHALL NOT substitute for protected review trust.

#### Scenario: Valid planning ancestry cannot conceal an unrelated trust base

- **GIVEN** valid planning ancestry but an unrelated protected proof commit
- **WHEN** independent execution validates its immutable lineage
- **THEN** execution SHALL fail before evidence reconciliation
- **AND** unrelated or candidate-newer planning ancestry SHALL also be rejected
