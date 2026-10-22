## ADDED Requirements

### Requirement: Authenticate native stack proof ancestry

A stacked PR SHALL reuse retained RED only from its live same-repository native
stack root, with exact full plan equality, immutable artifacts and unchanged
selected tests/support. Producer, execution and final verdict SHALL independently
validate the same context. Root base SHALL be protected dev or main.

#### Scenario: Valid parent proof remains usable

- **GIVEN** live native stack members form an exact same-repository branch and commit chain
- **WHEN** a child selects retained RED from its root branch
- **THEN** the original root base and branch are returned without relabeling proof
- **AND** the existing Git/JUnit and full mapping/plan checks remain mandatory

#### Scenario: Invalid or stale ancestry is rejected

- **GIVEN** a parent is ambiguous, forked, changed, missing or outside the native stack
- **WHEN** stack proof context is resolved
- **THEN** resolution fails before proof consumption

### Requirement: Preserve independent member authority

The organization policy SHALL require an unedited member grant for the exact
current head/tree, expiry and current write/admin permission. A stack base SHALL
be accepted only after native ancestry validation and SHALL NOT grant authority.

#### Scenario: Stack membership does not grant approval

- **GIVEN** a valid native chain without a matching member comment
- **WHEN** the authority gate validates the current PR
- **THEN** the gate fails
