## Context

The verifier needs to determine whether a red result is still meaningful after implementation. Static dependency inference asks which arbitrary runtime inputs could influence pytest. The bounded alternative declares which paths policy permits at each Git transition and re-executes both endpoints.

## Goals and Non-Goals

### Goals

- Make the historical claim finite, replayable, and auditable.
- Use Git ancestry and complete declared path sets rather than a partial Python interpreter.
- Execute red and final selectors in one pinned, isolated, secretless run.
- Require enforced network isolation for strict proof and bind its policy identity.
- Fail closed as `unproven` when any mandatory fact is unavailable.
- Prevent a changed verifier or policy from attesting itself.

### Non-Goals

- Discover imports, plugins, configuration, file reads, subprocess inputs, or all possible runtime behavior.
- Permit test/harness correction after R without creating a new R.
- Turn a test result into proof of complete requirements intent or global correctness.
- Merge Requirements, Code Review, contracts, tests, and security into one opaque verdict.

## Decisions

### Use an explicit B-R-H boundary with two closed path sets

B is the resolved PR merge base, R is an explicit full commit SHA supplied by the accepted mapping/checkpoint, and H is the evaluated full head SHA. The validator proves B is an ancestor of R and R is a strict ancestor of H.

The complete B..R changed-path set, including both rename endpoints, must be a subset of explicitly mapped `red_setup_touchpoints`. Each touchpoint is classified as a requirement, specification, selected test, test helper, conftest, or deterministic test configuration required to establish the red checkpoint. Governed implementation, dependency locks, workflows, runners, verifier/policy/schema files, generated artifacts, and unclassified paths are forbidden.

The complete R..H changed-path set, including both rename endpoints, must be a subset of explicitly mapped implementation touchpoints. Tests, fixtures, conftest files, pytest configuration, dependency locks, runner/workflow files, mappings, policies, verifier/schema files, and unclassified paths invalidate the checkpoint and require a new R.

These rules use Git path facts only. They do not infer runtime dependency closure.

### Replay both endpoints in one network-isolated environment

The workflow creates isolated read-only worktrees for R and H and invokes identical exact selectors with the same runner, lock/toolchain, environment allowlist, timeout/resource limits, and plugin-autoload policy.

Strict proof requires enforced egress isolation. The attestation binds the immutable network-policy identity and enforcement result. If isolation cannot be established, the run may remain diagnostic in shadow mode but chronology is `unproven` and strict policy cannot pass.

Every selector must collect exactly once. At R it must fail for the expected mapped assertion class, not skip, error during setup/collection, or disappear. At H it must pass. Any mismatch is `unproven` or failed according to the paired module contract and blocks strict policy.

### Core produces a versioned capsule; modules validate it

Core owns Git resolution, ancestry/path facts, isolated worktrees, test execution, JUnit retention, and production of the versioned replay capsule. The capsule includes a `schema_version` accepted by the paired signed Requirements release.

The capsule binds B/R/H commits and trees, both transition manifests/digests, mapping and plan digests, selector list, red and final JUnit digests, runner/toolchain/environment/network-policy identities, policy identity, verifier identity and epoch, timestamps, resource limits, and the signed module repository/commit/tree/package/signature identity.

The Requirements module validates capsule structure, hash links, transition facts, selector equality/outcomes, trusted module identity, and verifier epoch. It does not execute Git, pytest, or subprocesses. Unsupported capsule versions or untrusted module identities are `unproven`.

The fixed human claim is:

> These declared selectors failed at R and passed at H while only declared implementation touchpoints changed.

The report also states that this does not prove intent completeness, absence of defects, or code quality.

### Treat missing facts as unproven without rewriting current execution

Shallow history, unresolved refs, undeclared paths, checkout failure, selector mismatch, missing JUnit, timeout, tool error, network-isolation failure, capsule-version mismatch, module-identity mismatch, or verifier mismatch cannot produce pass, skip, or no-impact. Diagnostics and partial facts are retained before a non-zero strict exit.

R08 updates only `red_green_chronology`. It cannot erase, inflate, or overwrite R07 `current_execution` or the independent Code Review verdict.

### A verifier cannot authorize itself

The authoritative verifier, policy, workflow contract, module fixture, capsule schema, and attestation schema come from a pinned reviewed policy epoch. A PR that changes any of those surfaces is not eligible for ordinary self-attestation. The prior released verifier remains authoritative and the candidate runs in shadow until independent review and promotion create the next policy epoch.

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
