# Change: Release official security dependencies on main

## Why

The published v0.55.4 runtime must receive the reviewed dependency repairs without
unreleased dev runtime changes. This is the main release phase of issue #780.
The owner authorized version 0.55.11 and an exact MCP exception through
2026-11-04 inclusive. The previous dev admission work supplies no native RED
proof for this main branch.

## What Changes

- Refresh official Python packages to certifi 2026.10.19, GitPython 3.2.0,
  Hatchling 1.32.4, PyJWT 2.15.1, urllib3 2.8.0, virtualenv 21.11.0,
  python-discovery 1.6.0, and Semgrep 1.179.0. Preserve MCP 1.29.0.
- Bound the existing advisory register to MCP 1.29.0 and its reviewed advisory,
  with review date 2026-10-21 and expiry 2026-11-04 inclusive.
- Refresh documentation gems to jekyll-feed 0.18.0,
  jekyll-redirect-from 0.17.0, and jekyll-relative-links 0.9.1.
  Require JSON >=2.21.2,<3 and verify the installed gem behavior separately.
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

- The exact frozen certificate wheel excludes the compromised emSign root.
- The exact GitPython wheel rejects an outside submodule path before cloning.
- The exact PyJWT wheel preserves caller options and expiry verification on reuse.
- The only waived advisory is the exact approved MCP finding inside its dates.
- A real offline source-to-wheel build includes the unchanged bundled manifest.
- Native CI retains genuine test-first failures before dependency or release edits.
- Required quality checks, independent review, strict signatures, and dependency audits pass before the PR is offered for merge.
