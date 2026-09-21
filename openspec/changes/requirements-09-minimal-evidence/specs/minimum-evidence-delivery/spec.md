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

### Requirement: Workflow State Is Not Delivery Evidence

Ordinary current-run consumers SHALL remain usable without prior local workflow receipts or session phases. Workflow execution SHALL remain separate from Requirements reconciliation and SHALL preserve independent producer outcomes. Local progress SHALL NOT establish historical proof or protected CI authority.

#### Scenario: A harness starts in a fresh checkout

- **GIVEN** current required validation inputs and no local turn receipt
- **WHEN** ordinary verification or current reconciliation is requested
- **THEN** the missing session history does not block the operation
- **AND** only current identity-matching producer outputs determine their respective claims.

#### Scenario: A local receipt declares success over a failing producer

- **GIVEN** a local workflow receipt marked successful and a required failed or unknown producer result
- **WHEN** ordinary delivery evaluates current evidence
- **THEN** the producer remains non-passing and local state cannot override it or grant CI authority.

### Requirement: Acceptance Uniqueness Is Per Selected Execution Unit

Exactly-once acceptance SHALL apply per canonical selector within a selected execution unit: candidate source identity, environment/matrix lane, logical suite or shard and designated job attempt. Distinct required matrix units SHALL remain separate; each unit SHALL satisfy its own complete expected selector set. Core SHALL select the current authoritative units/attempts from trusted workflow metadata, not whichever artifact passes. A newer designated attempt that is pending, failed, cancelled or unavailable SHALL NOT fall back to an older passing attempt. Ambiguous attempt selection or duplicate selected outcomes inside one unit SHALL remain non-passing. The module SHALL compare supplied unit identity without performing Git, test or network operations; local declarations alone SHALL NOT establish CI authority.

The shared execution-unit identity SHALL be a compact UTF-8 JSON array with
this fixed field order:
`[candidate_binding, environment_binding, matrix_lane, suite_or_shard, provider, run_id, run_attempt, job_id]`.
Candidate and environment bindings SHALL preserve their existing report/plan
values, types and normalization; the remaining six fields SHALL be strings.
The tuple SHALL NOT replace the existing binding checks.
Matrix lane and suite/shard SHALL use stable configured identifiers, never
ambiguous display names; an absent matrix lane is the empty string. For GitHub,
provider is `github-actions` and run ID, run attempt and actual job execution ID
are canonical decimal strings from trusted metadata (job ID is the actual
execution ID, not the logical `GITHUB_JOB` name); reruns retain distinct
attempt/job identities. Local execution uses provider `local`, the current
invocation ID, attempt `1` and the selected command's configured job ID, without
claiming CI authority. Core selection and module comparison SHALL use exact
ordered-field equality after parsing this same representation, using existing
binding normalization and ignoring object-member order and JSON whitespace. Missing or ambiguous required identity SHALL remain non-passing.
This reuses existing bindings and execution metadata; no new hash, registry,
receipt, extra execution or approval protocol is required.

#### Scenario: A selector runs in two required matrix environments

- **GIVEN** one ordinary passing outcome for a selected selector in each of two distinct required execution units
- **WHEN** current results are reconciled
- **THEN** the matrix outcomes are evaluated separately rather than rejected as one duplicated global test
- **AND** every required unit must satisfy its own expected selection.

#### Scenario: A newer designated attempt has not passed

- **GIVEN** an older passing attempt and a newer designated attempt that is pending, failed, cancelled or missing
- **WHEN** current delivery selects results
- **THEN** it does not select the older pass or merge attempts into a passing result.

#### Scenario: A selector appears twice inside one selected unit

- **GIVEN** two outcomes for one canonical selected selector in the same execution unit
- **WHEN** reconciliation evaluates acceptance
- **THEN** the duplicate is rejected even when both outcomes say passed.

#### Scenario: Different runs or job retries contain the same selector

- **GIVEN** results share a selector, candidate and environment but differ in run, attempt or actual job execution ID
- **WHEN** the supplied execution-unit identities are compared
- **THEN** they remain distinct and only the currently designated trusted unit can satisfy its selection
- **AND** malformed or ambiguous identity cannot collapse them into one passing unit.
