# Security dependency stack: review and promotion

Prepared on 10 October 2026 (Europe/Berlin). Confidence: Medium. Dependency
compatibility is exercised; a required local smart-test run and protected
Requirements authority remain unresolved. This document does not authorize merge,
release publication, a policy exception or unrelated dependency upgrades.

## Review order and disposition

GitHub native stack #757 preserves all five PR numbers:

`dev ← #744 ← #727 ← #752 ← #754 ← #753`

| PR | Disposition | Result |
| --- | --- | --- |
| [#744](https://github.com/nold-ai/specfact-cli/pull/744) | Python security/build and single 0.55.5 bugfix | GitPython 3.2.0; Hatchling 1.32.4; minimal Python lock/export; sdist includes unchanged bundle-mapper assets |
| [#727](https://github.com/nold-ai/specfact-cli/pull/727) | Compatible JSON security hardening | `>=2.21.2,<3`; locked JSON 2.21.2 and Jekyll 4.4.1 retained; JSON 3 deferred |
| [#752](https://github.com/nold-ai/specfact-cli/pull/752) | Redirect security update | redirect-from 0.17.0; unsafe-scheme/encoding probes |
| [#754](https://github.com/nold-ai/specfact-cli/pull/754) | Feed security update | feed 0.18.0; language and CDATA escaping probes |
| [#753](https://github.com/nold-ai/specfact-cli/pull/753) | Link compatibility update | relative-links 0.9.1; Markdown/navigation/baseurl/rebuild probes; frozen Ruby CI evidence |

The user explicitly selected GitPython 3.2.0 after validation, superseding 3.1.62.
Original #756 evidence remains intact; its merged repair and subsequent #755
baseline are preserved. [#748](https://github.com/nold-ai/specfact-cli/pull/748)
retains its dated inventory as a planning follow-up, with the current approved
scope inherited. [#747](https://github.com/nold-ai/specfact-cli/issues/747) stays open
for broader accepted work. No lower-version duplicate was found in the inspected
open dependency PRs; none is closed without verified replacement coverage.

## Exact artifacts and source review

Selected executable artifacts were downloaded inertly, checked against registry
SHA-256 metadata, and compared with their upstream release tags before local
candidate execution. Ruby CI downloads these selected gems into its local cache
and checks the same hashes before bundle installation. Other locked Ruby packages
and Linux platforms remain unchanged. Temporary macOS platform locks are local
validation artifacts and are not delivery inputs.

| Artifact | SHA-256 | License |
| --- | --- | --- |
| GitPython 3.2.0 wheel | `bd70c5ec05cd2b797423e7eb312147d2458d3cca92085888fba2213f85905537` | BSD-3-Clause |
| GitPython 3.2.0 sdist | `fb92310af6844d96adc95ca066ed2e617c00e1dbd146a326626c81e72e18cc2e` | BSD-3-Clause |
| Hatchling 1.32.4 wheel | `08ecf7548fb48205e7f213d70c71e67b8271b7242093dc3f1da578b42c734a2c` | MIT |
| Hatchling 1.32.4 sdist | `c4468f73144c054d2aab4ef0f0378c43b9878bf07f8ffd6b79690e970d375f07` | MIT |
| redirect-from 0.17.0 gem | `703dab0428b20bb5d550ab83d3c28b65bb5ecc0f734c5e61ee680de391b3e897` | MIT |
| feed 0.18.0 gem | `8e6829f455b8764a8fa1bbb198d0ebb3525128dacc6ffe9d15f4df7388bc3647` | MIT |
| relative-links 0.9.1 gem | `6d5d70578c669ef9ee4c67f617d91497e0506fe5c1a059e484a900e18efb202e` | MIT |

GitPython's authenticated upstream tag resolves to
`6a7180a9dfcb276755a8af99dd78155f775a6b14`; all 37 wheel Python files match apart
from the generated version substitution. Hatchling's 67 package Python files
match its release tag; PyPI trusted-publisher metadata is observed, without a
claim of local cryptographic attestation verification. The Ruby runtime files
match their respective tags (9, 6 and 6 files).

The [GitPython tagged changelog](https://github.com/gitpython-developers/GitPython/blob/3.2.0/doc/source/changes.rst)
lists the additional security fixes. Redirect/feed release source records the
unsafe-target and escaping fixes. Some global advisory API records were unavailable;
that does not negate upstream fixes or establish exhaustive advisory coverage.
Both frozen Python advisory audits pass. Hatchling's Socket potential-vulnerability
alert concerns its configurable code-version plugin, byte-identical to 1.32.0;
this project uses static version metadata. Source triage is scoped to this build.
Protected Socket checks pass on the recorded Python implementation runs; no trust
exception was added. The new Ruby workflow pins action commits, including upstream
Ruby setup `e81a8fa391b11a595c1b7ed84177cc0fe02faf83` (unsigned upstream commit).

## Executable evidence and limits

- Actual GitPython containment RED precedes the candidate. Source distribution
  rebuilding also fails before the missing source inclusion is repaired.
- One 0.55.5 wheel builds from the sdist and installs with dependency resolution
  disabled on Python 3.11.15, 3.12.13 and 3.13.14. Git init/config/commit/branch/
  checkout/diff and ChangeAnalyzer consumers pass. Signed assets are unchanged.
- All 17 documentation-script tests pass after the JSON bound change. Redirect,
  feed language, feed CDATA and relative-link rebuild have separate actual RED
  results, then pass using selected versions at root and `/preview`.
- Full documentation builds pass for each updated plugin layer at both deployment
  paths. Existing Minima/Sass deprecation warnings remain baseline output.
- Frozen parity, uv lock check, both audits, trust/licenses, Bandit, Semgrep,
  strict module signatures and release-version/PyPI-ahead checks pass locally.
  BasedPyright's committed npm runner passes after installation: zero errors;
  1526 existing project warnings. Changed YAML and workflow lint pass. Global
  YAML output retains existing unrelated/archived errors.
- New GitPython/build tests have zero SpecFact review findings. The existing docs
  test file's 20 warnings and one information finding are outside modified
  assertions and explicitly retained as an unchanged-baseline exception in the
  TDD ledger. No new clean-code regression is accepted.
- Local full smart testing reports 25 failures, one error, 3189 passes and nine
  skips after marketplace installation replaces beartype inside the running
  interpreter. Earlier constrained testing retains its separate frozen/latest
  module-resolution conflict. The environment is restored with frozen sync.
  These results are not claimed green or replaced by focused probes.
- [Hosted run 38086498399](https://github.com/nold-ai/specfact-cli/actions/runs/38086498399)
  passes Python quality/tests, all runtime matrix jobs, security/trust/licenses,
  signatures, Socket and reproducibility on original implementation head 6ccc37a2.
  Its two installed inventories contain 180 identical normalized identities and
  its two SPDX SBOMs are byte-identical. The authoritative type artifact has zero
  errors. These artifacts are retained as historical evidence after re-signing.
- [Native RED run 38088121368](https://github.com/nold-ai/specfact-cli/actions/runs/38088121368)
  records `failing-first-proven`, gate pass, on GitHub-verified authored head
  `e9950388f97c7103b2f39f7fe4eefa5ced92282b`. The isolated startup lookup was
  reproduced failing, corrected using actual trusted distribution roots and
  replayed without changing the candidate hash/install controls or verifier.
- [Prior final run 38087716606](https://github.com/nold-ai/specfact-cli/actions/runs/38087716606)
  records native `verified`, gate pass, on pre-email-rebinding head 19a46c0a.
  Current Python head `76a42fc8fadad2fc7a17de97dd9076f7fb68a016` has a verified
  GitHub signature and a fresh [final run 38088309187](https://github.com/nold-ai/specfact-cli/actions/runs/38088309187).
  Protected Trusted Requirements Authority still rejects the context. Agent
  acceptance and native execution never substitute for that authority.

Re-signing corrected the commit/key email mismatch without changing any tree.
The remaining layers are re-signed sequentially. Current checks must be read from
each PR's final head after publication; older runs do not imply current readiness.

## Dev-to-main promotion checklist

1. Review all five PRs and resolve the local smart-test environment failure or
   provide an explicit repository-approved disposition. Obtain trusted
   Requirements authority for the actual final context; never fabricate a human
   acceptance record or relax the policy.
2. Require final-head Python and Ruby CI, both Socket checks, advisory/trust/license
   gates, code review, Requirements and signature checks. Retain normalized
   installed-package/SBOM and type JSON artifacts. Repeat affected checks after
   any code, base, mapping, branch or signature change.
3. Merge the dependency stack bottom-to-top into dev through GitHub's stack
   workflow. Inspect each parent-relative lock diff after retarget/rebase. Merge
   #748's planning follow-up only once its parent is integrated; keep #747 open.
4. Open/review the dev-to-main promotion at the integrated dev SHA. Require strict
   module signatures and Requirements promotion parity, four synchronized 0.55.5
   version sources, built wheel/sdist metadata and separate Security/Fixed entries.
   Recheck that PyPI still reports a lower release before tagging/publishing.
5. Validate production documentation at the custom-domain root and configured
   prefixed URL. Archive the whole OpenSpec change only after broader accepted
   tasks finish. Refresh internal wiki status from the sibling repository after
   actual merges; archive worktrees after reviewed integration.

Risks: a rebase invalidates proof (rerun on final heads); JSON 3 breaks Jekyll's
2.x contract (keep the explicit bound); shared locks accumulate resolver churn
(regenerate each layer from its actual parent and inspect the diff). Several CI
runs and maintainer review are still required. No tag or release is published.

Rollback: originals are captured under `refs/codex-security-backup/20261010/pr-N`
and local `original-pr-N.json` records. Additional authored/restack/email heads
are preserved under the same ref prefix. Restore each original remote branch
with an explicit lease against its current head, restore original base metadata,
and unlink native stack #757 only as part of a deliberate rollback. Revert coherent
inputs together if changes have merged; never reset shared dev/main history.
