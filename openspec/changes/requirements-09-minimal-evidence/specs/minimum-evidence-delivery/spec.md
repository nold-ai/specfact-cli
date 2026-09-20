## ADDED Requirements

### Requirement: Minimum Current-Run Delivery Evidence

Ordinary delivery SHALL derive a compact current-run result from existing required validation outputs at the candidate source identity. It SHALL NOT require historical RED commits, frozen mappings, approval receipts, retained-history replay or authority comments. Historical chronology and current execution SHALL remain independent claims. A required selected acceptance case SHALL be collected exactly once and produce an ordinary pass without `wasxfail` or equivalent xfail outcome metadata, including empty-valued markers; XFAIL and XPASS SHALL NOT satisfy acceptance.

#### Scenario: Ordinary implementation has current passing results

- **GIVEN** required validation ran against the candidate revision
- **AND** every selected acceptance test was collected exactly once and produced an ordinary pass without xfail outcome metadata
- **WHEN** ordinary delivery evaluates its MEB
- **THEN** current execution may pass without prior RED evidence
- **AND** chronology remains not evaluated and no correctness or complete-coverage claim is inferred.

#### Scenario: Required current results are incomplete

- **GIVEN** required output is missing, empty, malformed, wrong-revision, or a selected case is missing, duplicated, failed, errored, skipped, XFAIL or XPASS
- **WHEN** delivery reconciles the result
- **THEN** acceptance proof SHALL remain non-passing with actionable diagnostics.

#### Scenario: Non-strict XPASS resembles a passed call

- **GIVEN** a selected case has a passed call outcome with `wasxfail` or equivalent xfail metadata, even if the marker is empty
- **WHEN** current-run reconciliation evaluates acceptance
- **THEN** the case SHALL remain non-passing evidence rather than an ordinary pass
- **AND** a zero pytest exit code SHALL NOT override that result.

### Requirement: Independent Gates and Bounded Collection

Core SHALL preserve independent test, contract, security, module-authentication and review outcomes. It SHALL execute no duplicate suite solely for evidence, retain detailed run artifacts for 14 days by default, and keep release integrity records with releases. Source identity declared by candidate code alone SHALL NOT establish trusted CI authority.

#### Scenario: Evidence exists but a security check fails

- **GIVEN** current selected tests pass and an applicable security check fails
- **WHEN** the delivery decision is made
- **THEN** test evidence SHALL NOT override the failing check.

#### Scenario: Promotion is validated

- **GIVEN** a dev-to-main candidate
- **WHEN** required validation executes
- **THEN** it SHALL evaluate the promotion candidate without historical source-PR replay or bespoke ancestry reuse.

### Requirement: Optional Assurance Is Not a Default Prerequisite

Preflight seals, checkpoints and historical chronology SHALL apply only under explicit assurance selection. Generic review, skill distribution and generated default instructions SHALL remain usable without those optional capabilities. Explicit legacy requests SHALL retain their integrity requirements.

#### Scenario: Optional seal capability is absent

- **GIVEN** ordinary validation policy and no installed seal/checkpoint capability
- **WHEN** ordinary delivery or default generated guidance is used
- **THEN** missing optional assurance SHALL NOT block the operation or be described as a failed current-execution result.

### Requirement: Coordinated Trusted Enforcement Cutover

Core SHALL migrate repository-required checks and organization-required workflow policy together after a representative pilot, preserving independent workflow trust and required-check emission without unconditional-success placeholders.

#### Scenario: Repository workflow changes but organization policy is stale

- **GIVEN** the organization still requires historical authority
- **WHEN** rollout readiness is assessed
- **THEN** cutover SHALL remain incomplete until the reviewed policies agree
- **AND** no per-PR bypass SHALL substitute for that coordinated change.
