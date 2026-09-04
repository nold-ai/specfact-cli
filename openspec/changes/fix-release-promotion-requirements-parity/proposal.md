## Why

PR #691 is the canonical `dev` to `main` release promotion, but the Requirements
workflow treats the complete branch delta as one new implementation change. The
delta contains ten independently governed active OpenSpec changes, while the
workflow deliberately accepts review evidence for only one changed change. The
release is therefore blocked with ten `acceptance-missing` findings even though
the current tree already crossed the protected `dev` boundary.

## What Changes

- Recognize only a pull request from this repository's exact live `dev` ref to
  this repository's exact live `main` ref as a release promotion.
- Require immutable event commits and trees, checked-out head, live remote tips,
  ancestry, and the merged pull request that produced the current `dev` tree.
- Authenticate that merged pull request's successful GitHub-Actions
  Requirements and external-authority checks plus their exact, unexpired,
  digest-bound Requirements artifacts.
- Keep producer, fresh execution, plan comparison, artifact, final-verdict, and
  external authority jobs intact. Aggregate planning validation remains
  necessary but cannot pass a promotion without a distinct authenticated reuse
  attestation.
- Preserve the existing single-change maturity and review-evidence behavior for
  every other pull request, including forks and similarly named branches.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `trustworthy-green-checks`: permit an exact protected same-repository `dev` to
  `main` promotion to reuse authenticated Requirements evidence from the pull
  request that produced the current `dev` tree.

## Impact

- **Affected code:** `.github/workflows/requirements-evidence.yml`, one focused
  promotion-attestation validator, and focused unit/workflow contract tests.
- **Security:** the promotion verifier rejects missing, stale, spoofed, expired,
  ambiguous, or digest-mismatched prior evidence. Every non-promotion pull
  request retains existing fail-closed maturity, review-evidence, proof, and
  artifact checks. The independently required exact-head authority workflow and
  all release security/quality gates remain unchanged.
- **Compatibility:** no CLI, API, dependency, lock, package, or runtime behavior
  changes.
- **Documentation:** no public docs, README, landing-page, or navigation change;
  this internal release-governance correction is documented in its OpenSpec and
  TDD evidence.
- **Rollback:** revert the follow-up pull request. PR #691 will return to its
  current fail-closed state; no package or tag is modified by this change.

## Source Tracking

- **GitHub Issue**: #692
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/692>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: open; in progress; assigned; labels bug/openspec/QA/security
