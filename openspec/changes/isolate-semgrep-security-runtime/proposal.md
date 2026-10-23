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
  python-discovery 1.6.1, packaging 26.3, pycparser 3.12, and Semgrep 1.179.0. Preserve MCP 1.29.0.
- Raise the pycparser floor in pyproject.toml and setup.py to `>=3.12,!=3.0.*`.
  Replace the expired 2.22 provenance record with an exact 3.12 artifact review
  dated 2026-10-22 UTC and expiring 2026-11-04 inclusive.
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

## Supported parser correction on 2026-10-23 Europe/Berlin

The actual-date trust gate rejects the old pycparser 2.22 record after its
2026-10-22 expiry. The supported replacement is official pycparser 3.12.
Its wheel SHA-256 is `a076f3f489b39b43ed13563a1dafe42447445bec2e294154ec5c57fcdda4c85e`.
All eight package files and the BSD-3-Clause license match upstream commit
[3ec766b7cd94724cba714296509604597ea4ce4e](https://github.com/eliben/pycparser/commit/3ec766b7cd94724cba714296509604597ea4ce4e).
The retained investigation accessed the official artifacts and exact Socket wheel
page on 2026-10-23 Europe/Berlin, during 2026-10-22 UTC.

The source review discloses optional preprocessor shell-access capability,
filesystem access, URL strings, and a license-heading false positive. The
inspected exact wheel showed no eval, AI anomaly, obfuscation, or malware category.
This factual provenance review does not create a CVE waiver or renew the old
2.22 record. The exact MCP and OpenTelemetry exceptions remain separate.

Normal scratch resolution changes only pycparser 2.22 to 3.12 relative to the
nine-update candidate. Measured CFFI 2.1.0 and cryptography 50.0.0 compatibility
and optional-preprocessor/file-open boundary probes pass on macOS Python 3.11.15.
Other platforms and repository release gates remain to be verified. Fresh
independent mapping acceptance and genuine native RED must precede production.

## Scanner compatibility evidence boundary

The retained Semgrep 1.179.0 positive/negative CLI probes and schema 1.2 Code Review
result cover the pinned companion fixture 0.48.15 and its ordinary PATH-based passes.
They do not establish admission into the current companion's signed capsule.
The published [main 0.51.2 registry](https://github.com/nold-ai/specfact-cli-modules/blob/209b4ed835187ea857d1fa847abdd351f6f6232a/registry/index.json)
and [dev 0.51.4 registry](https://github.com/nold-ai/specfact-cli-modules/blob/430e3ccbf9fbd6a6177b033662a76235a8bd6cc8/registry/index.json)
were inspected on 2026-10-23 Europe/Berlin. Their archive-derived execution paths
use isolated capsules, `-I -S`, a cleared environment, dedicated PATH, and the
capsule's expected analyzer-version map. Capsule failure returns UNKNOWN without
falling back to core Semgrep. Signature verification and capsule execution were
not performed in this investigation. A future capsule-version change belongs in
the companion repository with its own policy and CI-produced integrity updates.
This core release changes no companion gate, capsule asset, or signature.
