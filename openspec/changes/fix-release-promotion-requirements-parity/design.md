## Context

The Requirements workflow derives one maturity for the entire pull-request diff
and can bind one provider-neutral review-evidence record to one changed active
OpenSpec change. That is correct for ordinary implementation pull requests. A
release promotion is different: its diff is the accumulated, already-reviewed
`dev` history, so multiple active planning and implementation changes are
expected.

Live rules protect both `dev` and `main` with pull requests, signed commits,
required checks, resolved review threads, strict up-to-date checks, and the
organization's external exact-head Requirements authority workflow. The release
pull request also reruns the complete security, dependency, signature, build,
runtime, and test gates.

## Goals / Non-Goals

### Goals

- Let the exact same-repository `dev` to `main` promotion reuse authenticated
  Requirements validation from the merged pull request that produced the
  current `dev` tree, without manufacturing one aggregate review acceptance.
- Make fork, wrong-repository, wrong-base, wrong-head, stale-tip, divergent,
  spoofed-check, expired-artifact, and digest-tampered cases fail closed.
- Keep producer, fresh consumer, plan parity, final verifier, and prior artifact
  authentication in agreement about the promotion classification.

### Non-Goals

- Support arbitrary multi-change implementation pull requests.
- Trust a branch merely because its display name is `dev`.
- Treat aggregate planning validation alone as production verification.
- Skip external authority or any release security/quality gate.
- Add a reusable exception or modify dependency/runtime behavior.

## Decisions

### Classify from immutable GitHub event and live Git identity

The promotion predicate requires a pull-request event whose base and head
repository IDs and full names equal the event repository, base ref is exactly
`main`, and head ref is exactly `dev`. A fork or any other incomplete identity
match remains on the ordinary pull-request path. After the complete identity
matches, producer, fresh execution, and final verification each require valid
40-hex event commits, exact checked-out and live remote tips, commit objects,
and `main` ancestry of `dev`; any downstream mismatch fails closed.

### Authenticate the protected development result

Before executing the candidate-tree promotion validator, each stage checks out
the immutable central `nold-ai/.github` authority validator, verifies its exact
commit, tree, script blob, and script SHA-256, and uses it to authenticate the
current promotion pull request's repository, refs, head commit/tree, unedited
member authority, expiry, and live permission. Candidate validator bytes are
therefore never the first or sole authority for their own execution.

The current `dev` tip must be a two-parent merge whose first parent is the
merged pull request's recorded `dev` base and whose second parent is its exact
head commit. The source head tree must equal the current `dev` tree, so merge
resolution cannot introduce unvalidated bytes. The GitHub API must return
exactly one matching merged same-repository pull request.

For that source head, the verifier requires unique successful check runs named
`Requirements evidence` and `Trusted Requirements Authority`, both created by
the GitHub Actions application. Their run metadata must bind the exact
repository, pull-request event, source head and branch, completed/success state,
and expected workflow path. The Requirements run must expose exactly one
unexpired producer artifact and one unexpired fresh-execution artifact. Each
artifact ID, run ID, repository/head identity, GitHub-recorded SHA-256 digest,
downloaded archive digest, and required content is authenticated.

The prior producer report must be a verified, implementation-verified pass for
the exact source head, with mapping, plan, JUnit, and source bindings intact.
The fresh-execution plan must be byte-identical to the producer plan.

### Preserve proof transport and use a distinct reuse claim

The promotion still generates a deterministic aggregate plan at planning
maturity. The fresh runner regenerates and byte-compares that plan, and the
final runner consumes the fresh execution artifact. Planning success alone is
insufficient: a separate canonical `promotion-reused` attestation must pass.
Producer, fresh execution, and final verification each independently re-fetch
and revalidate live GitHub metadata and prior artifacts, then compare canonical
attestation bytes. The report never claims that aggregate selectors were
executed in the promotion run.

The trusted main-relative verifier/core base, retained-RED ancestry, and both
Code Review passes remain based on the real `main..dev` delta. Only duplicate
aggregate Requirements selector execution is replaced by authenticated reuse.

### Keep release defenses independent

The organization authority check remains exact repository/pull request/branch/
head/tree bound. The pull-request orchestrator still runs dependency trust,
pip-audit, Socket, static analysis, module signatures, reproducible delivery,
package/runtime matrices, and the full test suite. This change does not make
Requirements the sole promotion defense.

## Risks / Trade-offs

- Promotion reuse supports only the repository's current two-parent merge
  topology on `dev`. A squash or rebase merge can satisfy the live ruleset but
  cannot prove the source-head/tree relationship required here, so the release
  promotion fails closed. Mitigation: merge release-bound changes into `dev`
  with a merge commit; otherwise rerun their Requirements evidence or extend
  the provenance model in a separately reviewed change.
- A privileged actor who bypasses repository-level `dev` protection could place
  unreviewed bytes on the promotion branch. Mitigation: the organization
  authority has no bypass actor; promotion reuse additionally requires the
  current promotion tree's expiring member authority and the exact-tree merged
  pull request's successful Requirements and authority runs, while the
  promotion reruns all release gates.
- A stale pull-request run could be mistaken for current evidence. Mitigation:
  every stage re-fetches run and artifact metadata and verifies exact live tips,
  source tree, expiry, and digests.
- Predicate drift between stages could create inconsistent evidence.
  Mitigation: one canonical validator and focused contract tests require the
  same inputs and byte-identical attestation in producer, consumer, and final.

## Rollback

Revert the follow-up pull request. This restores the existing conservative
failure on multi-change promotion pull requests without rewriting release
history.
