# Change: Release official security dependencies on main

## Why

The published v0.55.4 runtime must receive the reviewed dependency repairs without
unreleased dev runtime changes. This is the main release phase of issue #780.
The owner authorized version 0.55.11 and exact MCP and OpenTelemetry exceptions through
2026-11-04 inclusive. The previous dev admission work supplies no native RED
proof for this main branch.

## What Changes

- Refresh official Python packages to certifi 2026.10.19, GitPython 3.2.1,
  Hatchling 1.32.4, PyJWT 2.15.1, urllib3 2.8.0, virtualenv 21.14.12,
  python-discovery 1.6.1, packaging 26.3, and Semgrep 1.179.0. Preserve MCP 1.29.0.
- Bound the advisory register to two separate exact records: MCP 1.29.0 reviewed
  2026-10-21 and opentelemetry-api 1.37.0 reviewed 2026-10-22. Both expire
  2026-11-04 inclusive and retain only their approved advisory IDs.
- Refresh documentation gems to jekyll-feed 0.18.0,
  jekyll-redirect-from 0.17.0, and jekyll-relative-links 0.9.1.
  Require JSON >=2.21.2,<3 and verify the installed gem behavior separately.
- Add the scoped Ruby compatibility probe at `scripts/check_jekyll_dependencies.rb`
  and its CI workflow at `.github/workflows/docs-dependency-checks.yml`, ported
  from the reviewed dev implementation after native RED acceptance.
- Include the existing bundle-mapper source in the source distribution so the
  standard source-to-wheel build preserves its existing manifest bytes.
- Synchronize the four version sources to 0.55.11 and record the release in the changelog.

## Capabilities

### New Capabilities

- `isolated-scanner-runtime`: official dependency repair and bounded advisory treatment for the main release.

## Impact

The base is main commit 5262efb0. Runtime content and signed module assets must
match published v0.55.4 commit d579970565530c3fd7b98bad4de90cf874c2a99d,
except the authorized version strings. All existing main CI and local hooks
remain enforced. Both existing Python audit lanes remain strict. The dev-only
runtime-smoke dependency graph, late-cycle admission, and scanner forks are
outside this release. No local signing, merge, or publication is authorized.

## Source Tracking

- Source Repository: nold-ai/specfact-cli
- Issue URL: <https://github.com/nold-ai/specfact-cli/issues/780>
- Parent: <https://github.com/nold-ai/specfact-cli/issues/747>
- Status: Todo, checked by the coordinating agent on 2026-10-22.
- Future migration issues #523 and #783 are outside this release.

## Acceptance Criteria

- The lock and hashed export select every exact reviewed Python version.

- The exact frozen certificate wheel excludes the compromised emSign root.
- The exact GitPython wheel rejects outside paths and Git metadata checkout paths before cloning.
- The exact PyJWT wheel preserves caller options and expiry verification on reuse.
- Only the two exact approved MCP and OpenTelemetry findings are waived inside their separate review windows.
- A real offline source-to-wheel build includes the unchanged bundled manifest.
- Native CI retains genuine test-first failures before dependency or release edits.
- Required quality checks, independent review, strict signatures, and dependency audits pass before the PR is offered for merge.

## Approved correction on 2026-10-22

The owner approved replacing virtualenv 21.11.0 after the strict audit reported
five additional advisories. The official virtualenv 21.14.12 wheel requires
python-discovery >=1.6.1 and packaging >=26.3. The corrected selections are
21.14.12, 1.6.1, and 26.3. The other targets remained unchanged in that correction.
The retained scratch resolution changes only these three packages relative to
the prior candidate, with no added or removed packages. Fresh independent
mapping acceptance and native RED are required before applying production edits.

## Approved advisory correction on 2026-10-22

The owner approved official GitPython 3.2.1 after the audit reported
CVE-2026-114145 / GHSA-83vg-56qc-22m7 in 3.2.0. The frozen wheel must reject
`.git/hooks` and `GIT~1/hooks` checkout destinations before cloning. Ordinary
`vendor/module` and `.github/module` paths must still reach the clone boundary.

The owner separately approved opentelemetry-api 1.37.0 CVE-2026-114603 and alias
GHSA-xcq7-p3pf-p88h from 2026-10-22 through 2026-11-04 inclusive. The mitigation
permits ordinary local-rule CLI scanning only and excludes an instrumented HTTP
service accepting untrusted propagation headers. Preserve MCP 1.29.0 and its
original IDs and 2026-10-21 review date. Each record remains exact and expiring.
The approved scope requires fresh mapping acceptance and native RED before
production adoption. The earlier 23-case acceptance and native RED remain history.
