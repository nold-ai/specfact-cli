## MODIFIED Requirements

### Requirement: Producer-Bound Retained Red Proof

When a caller explicitly requests legacy historical RED/final reconciliation, core SHALL preserve immutable source, test, JUnit and toolchain bindings and reject missing, inconsistent, stale or tampered historical proof. These obligations SHALL NOT apply to ordinary current-run validation. No new change-specific bootstrap authority exception SHALL be introduced.

#### Scenario: Red execution publishes complete immutable bindings

- **GIVEN** an explicitly selected legacy historical RED run
- **WHEN** its report is published for legacy final reconciliation
- **THEN** source tree, merge base, selected test bytes, JUnit digest and actual runner/toolchain bindings SHALL remain complete and consistent
- **AND** the report SHALL NOT be required by ordinary current-run delivery.

#### Scenario: Missing or inconsistent producer evidence fails closed

- **GIVEN** an explicitly requested legacy historical report lacks valid required bindings
- **WHEN** legacy reconciliation evaluates it
- **THEN** historical verification SHALL fail without falling back to current-only evidence.

#### Scenario: Existing tamper and chronology checks remain enforced

- **GIVEN** an explicitly requested legacy artifact is tampered, stale or chronologically invalid
- **WHEN** the legacy reader evaluates it
- **THEN** the historical claim SHALL be rejected
- **AND** no current pass SHALL be substituted for that claim.

#### Scenario: Producer repair bootstraps from exact failing ledger

- **GIVEN** the historical producer-repair bootstrap is encountered as an existing record
- **WHEN** a new producer repair is planned under ordinary delivery
- **THEN** the existing record SHALL remain historical only
- **AND** the new repair SHALL use meaningful regression tests and current-candidate results without a new expiring authority or ledger exception.

#### Scenario: Ordinary current-run validation has no historical record

- **GIVEN** ordinary delivery with valid current-candidate results and no retained RED artifact
- **WHEN** core evaluates current execution
- **THEN** it SHALL NOT request historical artifacts, frozen test ancestry or bootstrap approval
- **AND** it SHALL make no historical chronology claim.
