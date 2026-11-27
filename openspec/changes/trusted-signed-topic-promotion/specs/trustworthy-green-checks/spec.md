## ADDED Requirements

### Requirement: Signed promotion topics authenticate source evidence

A signed, repository-owned promotion topic SHALL carry the exact tree of a merge-ready, signed source pull request against protected development. The protected base verifier SHALL authenticate the source checks and artifacts. The topic SHALL retain its own authority and full Code Review.

#### Scenario: Signed topic reuses the evidence of its exact source tree

- **GIVEN** a signed topic and a successful source pull request against protected development
- **AND** the source includes both protected tips in its ancestry
- **AND** the release commit is the sole commit on top of the live main tip
- **WHEN** the protected validation stages independently confirm both live identities and equal trees
- **THEN** the stages reuse the source Requirements evidence and retain the topic's full promotion review
- **AND** reject unrelated or stale source runs, stale refs, mismatched trees, unsigned commits, and unverified source evidence.
