## Context

The verifier needs to determine whether a red result is still meaningful after implementation. Static dependency inference asks which arbitrary runtime inputs could influence pytest. The bounded alternative asks which paths policy permits to change after the red checkpoint and re-executes both endpoints.

## Goals and Non-Goals

### Goals

- Make the historical claim finite, replayable, and auditable.
- Use Git ancestry and declared path sets rather than a partial Python interpreter.
- Execute red and final selectors in one pinned, isolated, secretless run.
- Fail closed as `unproven` when any mandatory fact is unavailable.
- Prevent a changed verifier or policy from attesting itself.

### Non-Goals

- Discover imports, plugins, configuration, file reads, subprocess inputs, or all possible runtime behavior.
- Permit test/harness correction after R without creating a new R.
- Turn a test result into proof of complete requirements intent or global correctness.
- Merge Requirements, Code Review, contracts, tests, and security into one opaque verdict.

## Decisions

### Use an explicit B-R-H boundary

B is the resolved PR merge base, R is an explicit full commit SHA supplied by the accepted mapping/checkpoint, and H is the evaluated full head SHA. The validator proves B is an ancestor of R and R is a strict ancestor of H.

B..R may change requirements, specs, and exact test artifacts needed to create the red checkpoint, but no mapped governed implementation touchpoint. R..H may change only the mapping's explicit implementation touchpoint set. Tests, fixtures, conftest files, pytest configuration, dependency locks, runner/workflow files, mappings, policies, and unclassified paths invalidate the checkpoint and require a new R.

Path rules operate on Git's complete changed-path and rename endpoint sets. They do not infer runtime dependency closure.

### Replay both endpoints in one environment

The workflow creates isolated read-only worktrees for R and H and invokes identical exact selectors with the same runner, lock/toolchain, environment allowlist, timeout/resource limits, plugin-autoload policy, and network-disabled default.

Every selector must collect exactly once. At R it must fail for the expected mapped assertion class, not skip, error during setup/collection, or disappear. At H it must pass. Any mismatch is `unproven` or `failed` according to the paired module contract and blocks strict policy.

### Bind one precise attestation

The attestation includes B/R/H commits and trees, B..R and R..H path-set digests, mapping and plan digests, selector list, red and final JUnit digests, runner/toolchain/environment identities, policy identity, verifier identity, timestamps, and resource limits.

Its human claim is fixed:

> These declared selectors failed at R and passed at H while only declared implementation touchpoints changed.

The report also states that this does not prove intent completeness, absence of defects, or code quality.

### Treat missing facts as unproven

Shallow history, unresolved refs, checkout failure, changed undeclared paths, selector mismatch, missing JUnit, timeout, tool error, or identity mismatch cannot produce pass, skip, or no-impact. Diagnostics and partial facts are retained before a non-zero strict exit.

### A verifier cannot authorize itself

The authoritative verifier, policy, workflow contract, module fixture, and attestation schema come from a pinned reviewed policy epoch. A PR that changes any of those surfaces is not eligible for ordinary self-attestation. The prior released verifier remains authoritative and the candidate runs in shadow until independent review and promotion create the next policy epoch.

The first implementation of R08 therefore uses existing gates and independent review for bootstrap; it establishes the verifier epoch for subsequent PRs and does not claim to prove itself.

## Allowed Future Implementation Surface

- `.github/workflows/requirements-evidence.yml`;
- one small replay/provenance script, preferably replacing or simplifying `scripts/requirements_proof_provenance.py`;
- focused unit and integration tests using temporary Git repositories;
- documentation and these OpenSpec artifacts;
- the module fixture lock after a signed release.

Unrelated security, dependency-trust, safe-write, smart-coverage, or general pytest-analysis tooling is excluded.

## Rollout and Rollback

1. Publish the paired modules schema in shadow-compatible form.
2. Implement and benchmark replay using the preserved #665–#671 cases.
3. Establish policy epoch 1 through existing gates and independent review.
4. Run shadow mode, then warning mode, then strict mode after zero known seeded false-greens.
5. Roll back by disabling R08 enforcement; R07 current-run evidence remains active.

