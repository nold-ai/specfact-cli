# Change: Core Docs Canonical Portal And Ownership Split

## Why

`specfact-cli` currently publishes the canonical docs domain at `docs.specfact.io`, but the live docs set still mixes two different responsibilities:

- core CLI/runtime/platform documentation owned by `specfact-cli`
- bundle and workflow documentation that now belongs primarily to `specfact-cli-modules`

That mixed model was acceptable during migration, but it is now creating ongoing drift. The modules repository already has its own Jekyll docs site, yet the public topology still leaves `specfact-cli` acting as the de facto source for many module-specific pages. Readers cannot clearly tell which docs are canonical, and maintainers have to keep overlapping content aligned in two repos.

This change defines the core side of the final information architecture: `specfact-cli` remains the canonical docs entry point and owner of core runtime docs, while module-specific deep docs move to the dedicated modules site with explicit cross-site navigation.

## What Changes

- Modify core docs ownership guidance so `specfact-cli` explicitly owns the docs portal, core runtime/platform docs, and marketplace lifecycle concepts, while bundle-specific deep docs belong to `specfact-cli-modules`.
- Update the core landing page, README, and shared navigation language to present a canonical split between `Docs Home`, `Core CLI`, and `Modules`.
- Convert remaining module-specific pages in the core docs set into either overview/handoff pages or migration notes instead of presenting them as the long-term canonical source.
- Define the core-side publishing contract needed for Cloudflare-backed public topology, including support for an independent core docs origin and a canonical docs entry point.

## Capabilities

### Modified Capabilities

- `module-docs-ownership`: core docs ownership language must move from a temporary migration note to a stable, reader-facing boundary between core docs and module docs.
- `documentation-alignment`: live docs navigation, landing pages, and marketplace guidance must align with a two-site model and stop implying that core docs are the canonical source for all module workflows.

## Impact

- Affected docs: `README.md`, `docs/index.md`, `docs/_layouts/default.html`, marketplace/module guidance pages, and any remaining bundle-focused handoff content in `docs/guides/` or `docs/reference/`.
- User-facing impact: readers can distinguish core runtime docs from module-owned deep docs and navigate cleanly between the canonical docs entry point, core docs, and modules docs.
- Integration points: `specfact-cli-modules` docs navigation and landing copy must align with the same ownership model; Cloudflare-managed docs domains will rely on the resulting navigation contract.
- Rollback plan: if the split causes confusion, core docs can temporarily retain handoff notes without removing duplicate content while navigation wording is refined.

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: pending
- **Issue URL**: pending
- **Last Synced Status**: local-proposal
- **Sanitized**: true
