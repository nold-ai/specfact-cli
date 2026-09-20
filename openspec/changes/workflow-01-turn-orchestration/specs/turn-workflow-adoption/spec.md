## ADDED Requirements

### Requirement: Module-Owned Workflow Adoption

Core SHALL adopt workflow execution through its existing module interfaces and SHALL retain repository configuration and projection ownership. It SHALL NOT introduce a competing built-in orchestration engine or redefine producer verdict policy.

#### Scenario: Workflow module is unavailable

- **GIVEN** an invocation reference and no compatible enabled workflow module
- **WHEN** a contributor invokes the workflow
- **THEN** an actionable installation/compatibility diagnostic is returned without a synthetic passing result.

### Requirement: Verification Preserves Repository Inputs

Workflow verification SHALL use check-only adapters with explicit index, worktree or resolved range scope. It SHALL preserve source files and index contents; ignored outputs and caches MAY be written. Mutation operations SHALL remain explicit and invalidate affected results.

#### Scenario: Partially staged file requires a formatting change

- **GIVEN** different index and worktree contents and a format violation
- **WHEN** index verification runs
- **THEN** it reports the index violation without formatting, staging, regenerating tracked files or substituting worktree contents.

#### Scenario: Fresh-session verification

- **GIVEN** current source and configured checks but no earlier turn receipt
- **WHEN** standalone verification runs
- **THEN** required checks execute or reuse identity-matching current outputs without requiring prior session phases or RED history.

#### Scenario: Required independent gate fails

- **GIVEN** a passing review report and failed tests or security checks
- **WHEN** verification presents results
- **THEN** the failing producer remains non-passing and cannot be hidden by a score or findings projection.

### Requirement: Canonical Repository Skill Projection

Repository skill projections SHALL be reproducible from canonical tracked sources and an explicit supported-destination manifest. Drift checks SHALL cover source, destination, renderer and manifest changes in local hooks and CI. Generation SHALL preserve unmanaged files and reject unsafe destinations or collisions.

#### Scenario: Only a generated skill is edited or removed

- **GIVEN** unchanged canonical skills and a changed or deleted managed destination
- **WHEN** projection checking runs
- **THEN** it fails with the affected destination and a regeneration instruction without writing files.

#### Scenario: A destination contains unrelated custom content

- **GIVEN** unmanaged content or a path escaping the configured destination root
- **WHEN** generation is requested
- **THEN** it preserves unrelated files and rejects unsafe or colliding writes.

### Requirement: Readiness Uses Current Governance

The adoption SHALL check uncovered native GitHub metadata where linked-issue governance applies and SHALL keep drift observations distinct from semantic invalidity. Optional assurance and internal wiki access SHALL NOT become universal product prerequisites.

#### Scenario: A planned capability is new and its blocker completed

- **GIVEN** a valid ADDED capability absent from canonical specs and a genuinely completed blocker
- **WHEN** pre-validation checks planning drift
- **THEN** neither observation alone causes stale-plan failure; current metadata and remaining applicable prerequisites determine readiness.

#### Scenario: Linked issue governance cannot be verified

- **GIVEN** required current parent, project or concurrency metadata is missing or unavailable
- **WHEN** readiness for linked public implementation is evaluated
- **THEN** it reports the unmet check without treating a cached backlog-only PASS as complete governance verification.

### Requirement: Pilot Precedes Adoption Activation

Core runtime adoption SHALL consume a compatible signed workflow publication and SHALL pass representative scope, no-mutation and independent-gate checks before activating contributor guidance. Repository projection MAY ship independently. R09 and C15 SHALL retain their own policy activation and trust requirements.

#### Scenario: Only a candidate workflow build exists

- **GIVEN** an unpublished workflow candidate
- **WHEN** stable repository runtime adoption is evaluated
- **THEN** candidate testing may proceed but the signed publication prerequisite remains unresolved.

### Requirement: Signed Current-Run Producer Compatibility Precedes Adoption

Runtime Requirements integration and adoption SHALL validate the exact immutable signed #481 publication, schema-v3 `current_execution` capability, archive/manifest/payload identities and compatibility with the actual core and selected #483 workflow versions before selecting that combination for use. Existing representative current-result fixtures SHALL exercise the installed combination. Missing, unsigned, incompatible or v2-only producers SHALL leave runtime adoption not ready; receipts and legacy-schema fallbacks SHALL NOT satisfy this gate. Repository projection MAY proceed independently, and core #740 SHALL retain its policy cutover ownership.

#### Scenario: Workflow package is signed but its Requirements producer is incompatible

- **GIVEN** a valid signed #483 workflow package and an absent, unsigned, incompatible or v2-only #481 Requirements producer
- **WHEN** runtime integration or core adoption readiness is checked
- **THEN** the combination is rejected as not ready with an actionable diagnostic
- **AND** independent repository projection can proceed without claiming runtime readiness.

#### Scenario: Installed signed producer and workflow match the actual core

- **GIVEN** exact signed #481/#483 identities compatible with the actual core candidate and the v3 current-execution contract
- **WHEN** the installed combination passes the existing representative acceptance fixtures
- **THEN** the compatibility prerequisite is satisfied for that exact combination
- **AND** this does not activate or replace the separate R09 required-policy cutover.
