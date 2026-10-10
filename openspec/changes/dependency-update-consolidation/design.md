# Compatible dependency consolidation

## Historical focused baseline repair (#756)

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

## Delivery-package probe and trusted verifier separation

The independent Requirements consumer retains its unchanged base verifier graph.
The JWT regression therefore exercises the delivery package in an isolated child:
extract the one hash-pinned PyJWT entry from the coherent CI export, install only
its binary wheel into a temporary target with hash verification and no dependencies,
and run Python with isolated mode and site loading disabled. Frozen parent assertions
check the bound version, unchanged caller options and expiry on reuse. Fail on missing
tooling, ambiguous/missing locks, install failures or unavailable execution. No verifier
package, workflow, authority policy or gate is changed. The separate compatibility
control and full delivery graph checks remain independently required.

## Authorized five-layer stack (2026-10-10, Europe/Berlin)

This amendment supersedes the historical focused-slice scope exclusions above.
Start each dedicated worktree from its preceding layer and preserve merged #756
inputs and proof. #744 owns Python/build inputs and the single 0.55.5 patch bump;
PR #727 owns the compatible JSON declaration; #752/#754/#753 own their selected
Jekyll plugins. Generate locks conservatively and inspect parent-relative diffs.

GitPython 3.2.0 closes GHSA-59cr-6r3x-644w. Its path containment regression must
fail against the unchanged delivery wheel before adopting the screened candidate.
Hatchling 1.32.4 restores the plugin interface broken in 1.32.3; both declarations
and the build expectation must agree. Preserve PyJWT 2.15.1, urllib3 2.8.0,
virtualenv 21.11.0, Semgrep 1.179.0 and python-discovery 1.6.0.

Jekyll 4.4.1 requires JSON ~>2.6. Use >=2.21.2,<3 and retain locked 2.21.2;
do not take #727's incidental Jekyll downgrade. JSON 3 migration is deferred.
Redirect-from 0.17.0 and feed 0.18.0 release notes identify security fixes even
where a global advisory record is unavailable. Relative-links 0.9.1 requires
Ruby >=3.0; the documented Ruby 3.2 build remains supported. Test dangerous and
ordinary redirect/feed inputs and rewritten links at root and nonempty base URLs.

Preserve #756 proof files byte-for-byte. Its completed native test cases become
historical inspection cases in this slice's active mapping, with the original
mapping available from merged #756. A fresh authored snapshot maps the new failing
GitPython boundary only; existing controls and configuration checks remain required
independent tests. No passing control is mislabeled as RED. Subsequent layers add
their own scoped specifications and evidence before dependency adoption.

Capture old heads before rewriting and use explicit leases. A failed lease stops
publication; re-read concurrent work rather than overwriting it. Native stack
registration is optional; linear base branches and body links are the fallback.
Rebases require fresh final-head evidence. Do not close retained PRs or #747.
Keep #748's dated inventory historical and defer its broader package assessment.

Before promotion verify frozen parity, both audits, trust/Socket, licenses,
Python 3.11-3.13 wheel installation, GitPython consumers, backend metadata,
Jekyll output, required quality/review/Requirements and module signatures.
The promotion checklist is reviewable preparation, not authorization to merge
or publish. Restore captured refs only with new explicit leases; restore coherent
dependency inputs together and never represent vulnerable rollback as release-safe.

## GitPython scope amendment

On 10 October 2026 the user approved GitPython 3.2.0 after validation.
It includes the 3.1.62 containment fix and six additional security fixes listed
in the tagged upstream changelog. Python 3.7 removal does not affect the supported
3.11–3.13 matrix. The pure Python GitDB backend is deprecated; repository consumers
must retain the default GitCmdObjectDB backend. Exact artifact and consumer checks
remain required; an advisory database miss does not establish absence of risk.
