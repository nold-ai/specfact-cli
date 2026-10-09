# Focused baseline repair

Reuse existing #747 and its change identity. This implementation branch covers only the
focused scenarios; do not copy #748's broader inspection-only mapping into a verified claim.

Two early assumptions: patched packages resolve together and analyzer failures indicate a
production regression. The three-package graph fails Semgrep/PyJWT and virtualenv/discovery
constraints. The five-package candidate resolves exactly PyJWT 2.15.1, urllib3 2.8.0,
virtualenv 21.11.0, Semgrep 1.179.0 and python-discovery 1.6.0. Unchanged dev reproduction
shows the analyzer fixture fails by staging .git/config before invoking production code.

Publish spec/tests/agent acceptance first with unchanged locks and the broken fixture;
retain authentic host RED. Never fabricate run IDs, late-RED authority, reviewer identity
or prior receipts. Repair through reviewed lock generation and the narrow staging root.
Preserve trust exceptions, signatures, release versions, gates and exact module fixture.

JWT options must remain caller-owned and expiry must remain enforced on reuse; normal signed
tokens and trailing signature padding must work. Check urllib3 proxy TLS/body boundaries,
virtualenv discovery/seeding and Semgrep invocation separately. Upgrading does not sanitize
seed-update logs inherited from an older virtualenv. Use a workspace-local app-data root and
no periodic update for the ephemeral smoke launcher fallback; preserve ordinary editable
installation and never delete the shared user cache. Hatch/user environments outside that
scoped caller need separate clean recreation after a suspected cache compromise.

Obtain independent patch review and applicable native/quality/security/Python matrix proof.
Integrate through normal review, then update #755 and obtain its new exact-head member grant.
Roll back coherent inputs only to a reviewed safe graph, retaining evidence. Broader #748
scope and all planned workflow runtime tasks remain outside this repair.

## Evidence boundary corrected after first hosted run

The released RED contract requires every selected pytest case to fail. The initial hosted
plan was rejected because only the JWT option regression failed; the legitimate control
and fixture cases passed in that frozen validator environment. Preserve the rejection.
Select the actually failing JWT regression and, after the cache amendment, its independently
failing caller regression for native RED/final execution. The
legitimate control and all three analyzer tests remain independently required in focused
checks and the full current-head suite; their inspection cases do not assert native
execution proof or waive failures. Do not change tests merely to manufacture RED.

Source review disproved virtualenv 21.7.13's completeness: default background seed updates
can cache unverified wheels when PyPI metadata is blocked. The minimum source-complete
candidate is 21.11.0, which raises UnverifiedWheelError on unavailable metadata/digest.
Re-resolve and screen this revised exact candidate before adoption.

The independent review and inert-cache probe confirmed that even 21.11.0 can select an
unverified wheel already logged by an old updater. This does not invalidate rejection of
new unverified downloads, but requires the smoke fallback's fresh local cache boundary.
Author and reproduce its regression before changing the caller.

The cache regression uses a separate subprocess test with unchanged parent assertions
and a bounded child caller. This matches existing integration-test conventions and
keeps mutable implementation separate from immutable pytest support. Retain a fresh
authored/RED/final lineage and all prior rejected evidence.
