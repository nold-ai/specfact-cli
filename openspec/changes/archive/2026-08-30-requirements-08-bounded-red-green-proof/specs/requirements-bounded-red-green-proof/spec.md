## ADDED Requirements

### Requirement: Explicit Three-Commit Boundary

Core SHALL evaluate historical red-green proof against three explicit full Git identities: B, the pull-request merge base; R, an accepted red commit; and H, the green implementation checkpoint. It SHALL also bind D, the current delivered head. It SHALL prove B is an ancestor of R, R is a strict ancestor of H, H is an ancestor of or equal to D, and D exactly equals the delivery identity.

The accepted mapping SHALL contain a positive `checkpoint_attempt`. Changing or retrying R SHALL require stakeholder acceptance of an incremented attempt, which changes the mapping digest and creates a new immutable namespace; an existing tag SHALL NOT be moved, deleted, or reused. Core SHALL derive the exact R and H checkpoint refs as `refs/tags/specfact-checkpoint/<change-id>/<mapping-digest>/red` and `refs/tags/specfact-checkpoint/<change-id>/<mapping-digest>/green` from the accepted change identifier and frozen mapping digest. Each ref SHALL resolve to a protected, non-rewritable, signed annotated tag created after its target commit by an approved checkpoint issuer. Its canonical annotation SHALL bind repository ID, change ID, checkpoint role, full commit and tree identities, mapping/plan/selector/path-role digests, verifier epoch, issuer identity, and signature. Core SHALL validate the tag object, signature/trust identity, repository-ruleset identity, and checkpoint-policy epoch with a read-only token before replay. A direct SHA supplied through PR text, label, comment, mutable branch, workflow input, or retained workflow artifact SHALL NOT be checkpoint authority. Before implementation starts, a repository administrator SHALL externally establish the non-rewritable tag ruleset, approved signer/trust set, canonical annotation schema, and checkpoint-policy epoch. After R exists and before production edits, an authorized issuer SHALL verify the frozen red inputs and create/push the exact signed red tag. After H exists and its implementation tests pass, the issuer SHALL create/push the exact signed green tag. The pull-request workflow SHALL remain read-only and SHALL only consume/verify these tags; it SHALL NOT issue or mutate them.

The complete B..R changed-path set and both endpoints of every rename SHALL be a subset of explicitly mapped `red_setup_touchpoints`. Each red-setup touchpoint SHALL have an allowed requirement, specification, selected-test, test-helper, conftest, deterministic-test-configuration, `proof_mapping`, `failing_tdd_evidence`, or `readiness_validation_evidence` role. `proof_mapping` SHALL identify this change's accepted `requirements-evidence.yaml` containing schema-validated exact selectors, one stable opaque `expected_failure_id` for every selector, and all three path-role sets. `failing_tdd_evidence` SHALL identify only this change's `TDD_EVIDENCE.md` failing-before record written before production edits. `readiness_validation_evidence` SHALL identify only this change's `CHANGE_VALIDATION.md` pre-R readiness section required by repository governance. The mapping, plan, selectors, expected-failure identities, path-role sets, failing-before evidence, readiness evidence, and their digests SHALL be frozen at R and remain unchanged through H. `CHANGE_VALIDATION.md` MAY then be extended only in H..D under its separate exact delivery-evidence role. Governed implementation, dependency locks, workflows, runners, verifier/policy/schema files, other generated artifacts, and unclassified paths SHALL be rejected.

The complete R..H changed-path set and both endpoints of every rename SHALL be a subset of explicitly mapped implementation touchpoints. Tests, fixtures, conftest files, test configuration, dependency locks, runners/workflows, mappings/plans, policy/verifier/schema files, evidence records, generated artifacts, and unclassified paths SHALL be rejected and require a new R.

When D differs from H, the complete H..D changed-path set and both endpoints of every rename SHALL be a subset of exact mapped `delivery_evidence_touchpoints`. Only the governed change's `TDD_EVIDENCE.md` and `CHANGE_VALIDATION.md` SHALL have that role. Implementation, tests, fixtures, configuration, dependencies, mapping/plan inputs, workflows, runners, policy/verifier/schema files, generated runtime inputs, other documentation, and unclassified paths SHALL be rejected. At R, core SHALL extract exactly one `specfact:frozen-failing` section from `TDD_EVIDENCE.md` and exactly one `specfact:frozen-readiness` section from `CHANGE_VALIDATION.md`, bind their exact bytes and digests, and repeat extraction at D. H..D changes SHALL be append-only outside those markers. A missing, duplicate, reordered, rewritten, or deleted frozen section SHALL be unproven even when every changed path is allowed. The validator SHALL use Git path and rename facts only. It SHALL NOT discover imports, pytest plugins, configuration, data reads, aliases, mutations, namespaces, symlinks, or other runtime dependency closure.

#### Scenario: Declared red setup, implementation transition, and delivery evidence are eligible

- **GIVEN** valid full B, R, H, and D commits with B < R < H <= D, D equals the current delivery identity, and protected signed red/green checkpoint tags bind R/H to the frozen change/mapping/plan/selector/path-role identities
- **AND** every B..R changed path and rename endpoint is an explicitly mapped allowed red-setup touchpoint, including the accepted proof mapping, failing-before TDD evidence, and pre-R readiness-validation evidence
- **AND** every R..H changed path and rename endpoint is an explicitly mapped implementation touchpoint
- **AND** every H..D changed path and rename endpoint, when present, is an exact mapped delivery-evidence touchpoint
- **WHEN** the boundary is evaluated
- **THEN** the checkpoint is eligible for runtime replay.

#### Scenario: Undeclared red-setup path invalidates R

- **GIVEN** B..R changes governed implementation, a dependency lock, workflow, runner, verifier/policy/schema file, non-approved generated artifact, or any undeclared or unclassified path or rename endpoint
- **OR** the proof mapping, exact selectors, expected-failure identities, path-role sets, failing-before evidence, or readiness-validation evidence are absent, invalid, or not frozen at R
- **WHEN** the boundary is evaluated
- **THEN** the checkpoint is unproven and strict policy fails
- **AND** remediation requires a new declared red checkpoint.

#### Scenario: Missing or untrusted R/H checkpoint authority invalidates chronology

- **GIVEN** either derived checkpoint tag is missing, lightweight, unsigned, movable, deleted/recreated, wrong-role, wrong-digest, signed by an unapproved issuer, or inconsistent with its protected ruleset or policy epoch
- **OR** R or H is supplied only through candidate-controlled SHA text, PR metadata, a mutable branch, workflow input, or retained workflow artifact
- **WHEN** the boundary is evaluated
- **THEN** chronology is unproven and strict policy fails
- **AND** remediation requires the external administrator/issuer ceremony and valid signed checkpoint tags; the read-only PR workflow cannot create them.

#### Scenario: Test, harness, policy, or unclassified change after R invalidates the checkpoint

- **GIVEN** R..H changes anything except a declared implementation touchpoint
- **OR** H..D changes anything except an exact mapped delivery-evidence touchpoint
- **OR** D does not preserve exactly one byte-identical frozen failing-before section and one byte-identical frozen readiness section from R
- **WHEN** the boundary is evaluated
- **THEN** the checkpoint is unproven and strict policy fails
- **AND** a behavior-affecting change requires a new R; an invalid bookkeeping transition requires a corrected H/D boundary.

### Requirement: Authoritative Runtime Replay

Core SHALL replay identical exact selectors at R and H and, when D differs from H, again at D during the same trusted run using isolated worktrees and the same pinned runner, dependency/toolchain identity, environment allowlist, plugin-autoload policy, timeout/resource limits, and enforced network-isolation policy. When D equals H, the H result SHALL also be the delivery result. Subprocesses SHALL use argument arrays and artifacts SHALL be written outside the evaluated worktrees.

Strict proof SHALL bind the network-policy identity and successful isolation result. If network isolation cannot be established, chronology SHALL be unproven; a diagnostic run MAY continue only in shadow mode and SHALL NOT satisfy strict policy.

Each selector SHALL collect exactly once at every executed snapshot. Before R, the accepted mapping SHALL assign the selector a stable opaque `expected_failure_id`, and the intended failing assertion SHALL emit exactly one `[specfact-failure:<expected_failure_id>]` marker in canonical JUnit failure text. At R the observed marker SHALL exactly equal the mapped ID. Assertion class alone SHALL be insufficient; a missing, duplicate, or different marker, including a different failure from the same assertion class, SHALL NOT count as red. Skip, collection/setup error, timeout, or absence also SHALL NOT count as red. At H the selector SHALL pass. At a distinct D it SHALL remain passing.

#### Scenario: Exact selectors fail at R, pass at H, and remain passing at D

- **GIVEN** an eligible boundary, accepted exact selectors with one mapped `expected_failure_id` each, and enforced network isolation
- **WHEN** replay completes at R, H, and distinct D when present
- **THEN** every selector has one canonical failing result at R whose single observed failure marker exactly matches its mapped `expected_failure_id`, one canonical passing result at H, and one canonical passing result at distinct D
- **AND** all result sets and the network-policy identity are retained for attestation.

#### Scenario: Replay cannot establish chronology

- **GIVEN** checkout, environment, network isolation, collection, execution, selector identity, or expected/observed failure identity fails at any required snapshot
- **WHEN** replay finalizes
- **THEN** chronology is unproven
- **AND** partial diagnostics are retained before strict policy exits non-zero.

### Requirement: Bound Proof Attestation

Core SHALL produce a content-addressed, versioned replay capsule using a `schema_version` accepted by the paired signed Requirements release. The capsule SHALL bind B/R/H/D commits and trees; both checkpoint tag names, tag-object identities, canonical annotations, signatures, approved issuer/trust identities, repository-ruleset identity, and checkpoint-policy epoch and accepted checkpoint-attempt identity; frozen failing/readiness section bytes and R/D digests plus equality results; B..R, R..H, and H..D path manifests/digests, mapping and plan digests, exact selectors, mapped expected-failure IDs, canonical observed red failure IDs and their digest, red, green-checkpoint, and delivery JUnit digests, runner/toolchain/environment/network-policy identities, policy identity, verifier identity and epoch, timestamps, resource bounds, and the signed module repository/commit/tree/package/signature identity.

Core SHALL own Git resolution, isolated worktrees, test execution, and capsule production. The paired Requirements module SHALL validate the capsule schema, hash links, transition facts, selector and failure-identity equality/outcomes, trusted module identity, and verifier epoch without executing Git, pytest, or subprocesses. Unsupported capsule versions or untrusted module identities SHALL be unproven.

The attested human claim SHALL be: "These declared selectors failed at R, passed at H, and still passed at delivery head D; only declared implementation touchpoints changed from R to H and only declared delivery-evidence touchpoints changed from H to D." The report SHALL state that it does not prove stakeholder-intent completeness, absence of defects, or code quality.

#### Scenario: Versioned capsule is complete and replayable

- **GIVEN** an eligible boundary, successful required-snapshot replay, and a trusted signed Requirements release
- **WHEN** core builds the capsule and the Requirements module validates it
- **THEN** every mandatory identity, including each mapped expected-failure ID and matching canonical observed red failure ID, schema version, transition, result, and digest is present and valid
- **AND** D equals the current delivery identity
- **AND** an independent runner can reconstruct the commands and verify artifact digests
- **AND** the module performs no Git or test execution
- **AND** no broader correctness claim is emitted.

#### Scenario: Candidate verifier cannot authorize itself

- **GIVEN** any governed transition changes the replay runner, workflow, policy, module fixture, capsule/attestation schema, or verifier identity
- **WHEN** ordinary R08 proof is requested
- **THEN** it is unproven under the current epoch
- **AND** the candidate may run only in shadow until a separately reviewed promotion establishes a new epoch.

### Requirement: Fail-Closed Unproven State

Missing or shallow history, invalid or abbreviated refs, missing or untrusted checkpoint authority, unresolved merge base, mismatched delivery identity, undeclared paths or frozen-ledger-section mismatch in any transition, checkout failure, selector or failure-identity mismatch, missing artifacts, tool failure, timeout, network-isolation failure, environment mismatch, unsupported capsule version, untrusted module identity, or verifier mismatch SHALL produce an explicit unproven result and non-zero strict exit after diagnostics are retained. None of these conditions may be represented as pass, skip, or no-impact.

#### Scenario: Mandatory fact is unavailable

- **GIVEN** at least one mandatory scope, identity, transition, execution, isolation, capsule, or artifact fact cannot be established
- **WHEN** the policy decision is produced
- **THEN** the R08 claim is unproven
- **AND** the report identifies the missing fact and replay/remediation step
- **AND** no summary says all validations passed.

#### Scenario: Unproven chronology preserves current execution

- **GIVEN** R07 has an independently reconciled `current_execution` result
- **AND** R08 chronology is missing, invalid, unsupported, or untrusted
- **WHEN** the Requirements report is finalized
- **THEN** only `red_green_chronology` is unproven
- **AND** `current_execution` and the independent Code Review verdict remain unchanged
- **AND** attempted chronology is not represented as no-impact.
