## Context

The verifier needs to determine whether a red result is still meaningful after implementation and still applies to the delivered head. Static dependency inference asks which arbitrary runtime inputs could influence pytest. The bounded alternative declares which paths policy permits at each Git transition and re-executes the red, green, and delivery snapshots.

## Goals and Non-Goals

### Goals

- Make the historical claim finite, replayable, and auditable.
- Use Git ancestry and complete declared path sets rather than a partial Python interpreter.
- Execute red, green-checkpoint, and delivered-head selectors in one pinned, isolated, secretless run.
- Require enforced network isolation for strict proof and bind its policy identity.
- Fail closed as `unproven` when any mandatory fact is unavailable.
- Prevent a changed verifier or policy from attesting itself.

### Non-Goals

- Discover imports, plugins, configuration, file reads, subprocess inputs, or all possible runtime behavior.
- Permit test/harness correction after R without creating a new R.
- Turn a test result into proof of complete requirements intent or global correctness.
- Merge Requirements, Code Review, contracts, tests, and security into one opaque verdict.

## Decisions

### Use a B-R-H proof boundary with a delivered-head binding D

B is the resolved PR merge base and D is the current delivered head. R and H are resolved only from protected signed annotated checkpoint tags, never from candidate-controlled SHA text. The validator proves B is an ancestor of R, R is a strict ancestor of H, H is an ancestor of or equal to D, and D exactly matches the delivery identity.

The verifier derives the exact tag names `refs/tags/specfact-checkpoint/<change-id>/<mapping-digest>/red` and `refs/tags/specfact-checkpoint/<change-id>/<mapping-digest>/green` from the accepted change identifier and frozen mapping digest. Each annotated tag is created after its target commit by an approved checkpoint issuer under a non-rewritable repository ruleset and canonically binds repository ID, change ID, role, commit and tree SHA, mapping/plan/selector/path-role digests, verifier epoch, issuer identity, and signature. Replay fetches and validates the tag objects with a read-only token before network-isolated execution. A lightweight, unsigned, movable, deleted/recreated, wrong-role, wrong-digest, unapproved-signer, or direct-SHA/PR-body/label/comment/workflow-input substitute is unproven. Historical workflow artifacts may retain diagnostics but are not checkpoint authority.

The complete B..R changed-path set, including both rename endpoints, must be a subset of explicitly mapped `red_setup_touchpoints`. Each touchpoint is classified as a requirement, specification, selected test, test helper, conftest, deterministic test configuration, `proof_mapping`, or `failing_tdd_evidence` required to establish the red checkpoint. `proof_mapping` is this change's accepted `requirements-evidence.yaml`; `failing_tdd_evidence` is only this change's `TDD_EVIDENCE.md` failing-before record. The mapping declares one stable opaque `expected_failure_id` for every exact selector before R. The mapping, plan, selectors, expected-failure identities, path sets, failing-before evidence, and their digests are frozen at R. Governed implementation, dependency locks, workflows, runners, verifier/policy/schema files, other generated artifacts, and unclassified paths are forbidden.

The complete R..H changed-path set, including both rename endpoints, must be a subset of explicitly mapped implementation touchpoints. Tests, fixtures, conftest files, pytest configuration, dependency locks, runner/workflow files, mappings, policies, verifier/schema files, evidence records, and unclassified paths invalidate the checkpoint and require a new R.

When D differs from H, the complete H..D changed-path set and rename endpoints must be a subset of exact mapped `delivery_evidence_touchpoints`. The only allowed roles are the governed change's `TDD_EVIDENCE.md` and `CHANGE_VALIDATION.md`, written after the passing run. Implementation, tests, fixtures, configuration, dependencies, mapping/plan inputs, workflows, runners, policy/verifier/schema files, generated runtime inputs, other documentation, and unclassified paths are forbidden. A violation makes chronology unproven; a behavior change requires a new R.

These rules use Git path facts only. They do not infer runtime dependency closure. D exists so repository-required post-green evidence can be committed without falsely calling it implementation or weakening the R..H freeze.

### Replay red, green, and delivery snapshots in one network-isolated environment

The workflow creates isolated read-only worktrees for R, H, and D when D differs from H, and invokes identical exact selectors with the same runner, lock/toolchain, environment allowlist, timeout/resource limits, and plugin-autoload policy. When D equals H, the single green replay supplies both identities without duplicate execution.

Strict proof requires enforced egress isolation. The attestation binds the immutable network-policy identity and enforcement result. If isolation cannot be established, the run may remain diagnostic in shadow mode but chronology is `unproven` and strict policy cannot pass.

Every selector must collect exactly once at every executed snapshot. Before R, the accepted mapping assigns the selector a stable opaque `expected_failure_id`, and the intended failing assertion emits exactly one `[specfact-failure:<expected_failure_id>]` marker in canonical JUnit failure text. At R the observed marker must exactly equal the mapped ID; assertion class alone is insufficient. A missing, duplicate, or different marker—including a different failure from the same assertion class—does not count as red. Skip, setup/collection error, timeout, or absence also does not count as red. At H the selector must pass, and at a distinct D it must remain passing. Any mismatch is `unproven` or failed according to the paired module contract and blocks strict policy.

### Core produces a versioned capsule; modules validate it

Core owns Git resolution, ancestry/path facts, isolated worktrees, test execution, JUnit retention, and production of the versioned replay capsule. The capsule includes a `schema_version` accepted by the paired signed Requirements release.

The capsule binds B/R/H/D commits and trees; both checkpoint tag names, tag-object identities, canonical annotations, signatures, approved issuer/trust identities, repository-ruleset identity, and checkpoint-policy epoch; B..R, R..H, and H..D transition manifests/digests, mapping and plan digests, selector list, mapped expected-failure IDs, canonical observed red failure IDs and their digest, red, green-checkpoint, and delivery JUnit digests, runner/toolchain/environment/network-policy identities, policy identity, verifier identity and epoch, timestamps, resource limits, and the signed module repository/commit/tree/package/signature identity.

The Requirements module validates capsule structure, hash links, transition facts, selector and failure-identity equality/outcomes, trusted module identity, and verifier epoch. It does not execute Git, pytest, or subprocesses. Unsupported capsule versions or untrusted module identities are `unproven`.

The fixed human claim is:

> These declared selectors failed at R, passed at H, and still passed at delivery head D; only declared implementation touchpoints changed from R to H and only declared delivery-evidence touchpoints changed from H to D.

The report also states that this does not prove intent completeness, absence of defects, or code quality.

### Treat missing facts as unproven without rewriting current execution

Shallow history, missing or untrusted checkpoint tags, unresolved refs, delivery-head mismatch, undeclared paths in any transition, checkout failure, selector mismatch, missing JUnit, timeout, tool error, network-isolation failure, capsule-version mismatch, module-identity mismatch, or verifier mismatch cannot produce pass, skip, or no-impact. Diagnostics and partial facts are retained before a non-zero strict exit.

R08 updates only `red_green_chronology`. It cannot erase, inflate, or overwrite R07 `current_execution` or the independent Code Review verdict.

### A verifier cannot authorize itself

The authoritative verifier, policy, workflow contract, module fixture, capsule schema, and attestation schema come from a pinned reviewed policy epoch. A change to any of those surfaces in B..R, R..H, or H..D is not eligible for ordinary self-attestation. The prior released verifier remains authoritative and the candidate runs in shadow until independent review and promotion create the next policy epoch.

The first implementation of R08 therefore uses existing gates and independent review for bootstrap; it establishes the verifier epoch for subsequent PRs and does not claim to prove itself.

## Allowed Future Implementation Surface

- `.github/workflows/requirements-evidence.yml`;
- one small replay/provenance script, replacing or simplifying `scripts/requirements_proof_provenance.py`;
- focused unit and integration tests using temporary Git repositories;
- documentation and these OpenSpec artifacts;
- the module fixture lock after a signed release.

Unrelated security, dependency-trust, safe-write, smart-coverage, or general pytest-analysis tooling is excluded.

## Rollout and Rollback

1. Publish the paired signed modules capsule schema in shadow-compatible form.
2. Implement and benchmark replay using the preserved #665–#671 cases.
3. Establish policy epoch 1 through existing gates and independent review.
4. Run shadow mode, then warning mode, then strict mode after zero known seeded false-greens.
5. Roll back by disabling R08 enforcement; R07 current-run evidence remains active.
