## ADDED Requirements

### Requirement: Requirements Evidence Delivery Enforcement

The delivery gate SHALL invoke only the pinned reviewed module release, validate the exact fixture identity before execution, retain current-run Requirements artifacts, and enforce Requirements and Code Review decisions independently.

#### Scenario: Immutable fixture mismatch fails before module execution

- **GIVEN** the modules repository, commit, tree, package version, signature, or clean-state identity differs from the fixture lock
- **WHEN** the delivery gate initializes
- **THEN** it fails before invoking module code
- **AND** it retains an actionable fixture diagnostic.

#### Scenario: Current-run artifacts are retained before enforcement

- **GIVEN** planning or execution produces success, failure, timeout, or reconciliation diagnostics
- **WHEN** the workflow reaches its terminal policy step
- **THEN** it has already uploaded the plan, JUnit when produced, Requirements JSON/Markdown, and review JSON
- **AND** the summary identifies which claim failed or remained unresolved.

#### Scenario: Review is run over an explicit resolved file set

- **GIVEN** the workflow invokes Code Review after Requirements reconciliation
- **WHEN** it selects review targets
- **THEN** it passes an explicit PR-delta file set or uses the module's explicit base/head range interface
- **AND** it does not rely on a clean checkout's worktree-only changed scope
- **AND** generic Code Review scope semantics remain module-owned.

#### Scenario: Independent failures remain blocking

- **GIVEN** Requirements passes but Code Review fails, or Code Review passes but Requirements fails
- **WHEN** the terminal policy step runs
- **THEN** the workflow exits non-zero
- **AND** neither green signal overwrites the failing signal.

