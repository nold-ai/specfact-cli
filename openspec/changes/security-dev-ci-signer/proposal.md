# Create-only reviewed-parent security CI signer

## Why

The reviewed PR786 test refresh needs a fresh CI service signature before its
complete patch can be pushed without merging. Historical PR785 signing evidence grants no new
scope. This auxiliary executor must never become the target tree.

## What changes

Add one bounded `publish_once(intent_file, expected, context)` operation.
Authenticate an uploaded source commit/tree and its entire dev-relative leaf
delta. Create one signed commit with the frozen reviewed PR786 head as its sole parent,
then create the initially absent fixed destination ref. Preserve partial and
uncertain outcomes without retries or cleanup.

This existing change now covers a fresh test-only refresh of PR786. The sole
source and signed-output parent is `4ae6175a4d337296d0347e73b66c9da1f0e43f7f`.
The new executor ref is `refs/heads/codex/security-dev-ci-test-refresh-20261029`
and the create-only destination is
`refs/heads/codex/security-dev-refreshed-test-prefix-20261029`.
The exact 19-path test/SPEC-only allowlist adds only
`tests/unit/security/test_code_review_dependency_security.py` and
`tests/unit/security/test_release_promotion_security_gates.py` to the prior 17.
Frozen dev/main guards and complete dev-relative tree comparison remain.
The final source SHA/tree and digest-bound intent remain pending root's final
normally checked source correction and independent binding review; provisional
source identities are not final bindings.

The historical run `40248154362` is complete and consumed. Its original source,
intent, executor and output records remain historical evidence, with no grant
transferred to this refresh. A new immutable executor, fresh signed authority
and independent live/output verification are required. Any later PR branch
advance belongs to root after those gates and is outside this create-only signer.

## Dependencies and limits

Root owns input freezing, GitHub metadata readiness, normal checks, independent
remote executor/intent review, the single real CI invocation, live verification
and raw fetched-object comparison. Native bootstrap remains separately blocked.
The internal wiki mirror and change-order registration are root follow-ups
outside this delegate's exclusive paths. No claim is made that either is done.
