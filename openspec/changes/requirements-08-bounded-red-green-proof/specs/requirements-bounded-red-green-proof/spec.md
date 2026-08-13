## ADDED Requirements

### Requirement: Explicit Three-Commit Boundary

Core SHALL evaluate historical red-green proof against three explicit full Git identities: B, the pull-request merge base; R, an accepted red commit; and H, the evaluated delivery head. It SHALL prove B is an ancestor of R and R is a strict ancestor of H. H SHALL be supplied as an immutable full SHA and SHALL equal the current delivery-head identity; an absent, abbreviated, substituted, or mismatched H SHALL be unproven.

The complete B..R changed-path set and both endpoints of every rename SHALL be a subset of explicitly mapped `red_setup_touchpoints`. Each red-setup touchpoint SHALL have an allowed requirement, specification, selected-test, test-helper, conftest, or deterministic-test-configuration role. Governed implementation, dependency locks, workflows, runners, verifier/policy/schema files, generated artifacts, and unclassified paths SHALL be rejected.

The complete R..H changed-path set and both endpoints of every rename SHALL be a subset of explicitly mapped implementation touchpoints. The validator SHALL use Git path and rename facts only. It SHALL NOT discover imports, pytest plugins, configuration, data reads, aliases, mutations, namespaces, symlinks, or other runtime dependency closure.

#### Scenario: Declared red setup and implementation-only transition are eligible

- **GIVEN** valid full B, R, and H commits with B < R < H and H equals the current delivery-head identity
- **AND** every B..R changed path and rename endpoint is an explicitly mapped allowed red-setup touchpoint
- **AND** every R..H changed path and rename endpoint is an explicitly mapped implementation touchpoint
- **WHEN** the boundary is evaluated
- **THEN** the checkpoint is eligible for runtime replay.

#### Scenario: Undeclared red-setup path invalidates R

- **GIVEN** B..R changes governed implementation, a dependency lock, workflow, runner, verifier/policy/schema file, generated artifact, or any undeclared or unclassified path or rename endpoint
- **WHEN** the boundary is evaluated
- **THEN** the checkpoint is unproven and strict policy fails
- **AND** remediation requires a new declared red checkpoint.

#### Scenario: Test, harness, policy, or unclassified change after R invalidates R

- **GIVEN** R..H changes a test, fixture, conftest, pytest configuration, lockfile, executor, workflow, mapping, policy, verifier, attestation schema, or unclassified path
- **WHEN** the boundary is evaluated
- **THEN** the checkpoint is unproven and strict policy fails
- **AND** remediation instructs the author to create a new R.

### Requirement: Authoritative Runtime Replay

Core SHALL replay identical exact selectors at R and H during the same trusted run using isolated worktrees and the same pinned runner, dependency/toolchain identity, environment allowlist, plugin-autoload policy, timeout/resource limits, and enforced network-isolation policy. Subprocesses SHALL use argument arrays and artifacts SHALL be written outside the evaluated worktrees.

Strict proof SHALL bind the network-policy identity and successful isolation result. If network isolation cannot be established, chronology SHALL be unproven; a diagnostic run MAY continue only in shadow mode and SHALL NOT satisfy strict policy.

Each selector SHALL collect exactly once. At R it SHALL fail for the mapped expected assertion class and SHALL NOT count skip, collection/setup error, timeout, or absence as red. At H it SHALL pass.

#### Scenario: Exact selectors fail at R and pass at H

- **GIVEN** an eligible boundary, accepted exact selectors, and enforced network isolation
- **WHEN** replay completes at both commits
- **THEN** every selector has one canonical failing result at R and one canonical passing result at H
- **AND** both result sets and the network-policy identity are retained for attestation.

#### Scenario: Replay cannot establish chronology

- **GIVEN** checkout, environment, network isolation, collection, execution, or result identity fails at either endpoint
- **WHEN** replay finalizes
- **THEN** chronology is unproven
- **AND** partial diagnostics are retained before strict policy exits non-zero.

### Requirement: Bound Proof Attestation

Core SHALL produce a content-addressed, versioned replay capsule using a `schema_version` accepted by the paired signed Requirements release. The capsule SHALL bind B/R/H commits and trees, B..R and R..H path manifests/digests, mapping and plan digests, exact selectors, red and final JUnit digests, runner/toolchain/environment/network-policy identities, policy identity, verifier identity and epoch, timestamps, resource bounds, and the signed module repository/commit/tree/package/signature identity.

Core SHALL own Git resolution, isolated worktrees, test execution, and capsule production. The paired Requirements module SHALL validate the capsule schema, hash links, transition facts, selector equality/outcomes, trusted module identity, and verifier epoch without executing Git, pytest, or subprocesses. Unsupported capsule versions or untrusted module identities SHALL be unproven.

The attested human claim SHALL be: "These declared selectors failed at R and passed at H while only declared implementation touchpoints changed." The report SHALL state that it does not prove stakeholder-intent completeness, absence of defects, or code quality.

#### Scenario: Versioned capsule is complete and replayable

- **GIVEN** an eligible boundary, successful endpoint replay, and a trusted signed Requirements release
- **WHEN** core builds the capsule and the Requirements module validates it
- **THEN** every mandatory identity, schema version, and digest is present and valid
- **AND** an independent runner can reconstruct the commands and verify artifact digests
- **AND** the module performs no Git or test execution
- **AND** no broader correctness claim is emitted.

#### Scenario: Candidate verifier cannot authorize itself

- **GIVEN** H changes the replay runner, workflow, policy, module fixture, capsule/attestation schema, or verifier identity
- **WHEN** ordinary R08 proof is requested
- **THEN** it is unproven under the current epoch
- **AND** the candidate may run only in shadow until a separately reviewed promotion establishes a new epoch.

### Requirement: Fail-Closed Unproven State

Missing or shallow history, invalid or abbreviated refs, unresolved merge base, undeclared paths, checkout failure, selector mismatch, missing artifacts, tool failure, timeout, network-isolation failure, environment mismatch, unsupported capsule version, untrusted module identity, or verifier mismatch SHALL produce an explicit unproven result and non-zero strict exit after diagnostics are retained. None of these conditions may be represented as pass, skip, or no-impact.

#### Scenario: Mandatory fact is unavailable

- **GIVEN** at least one mandatory scope, identity, execution, isolation, capsule, or artifact fact cannot be established
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
