# Design: Core Docs Canonical Portal And Ownership Split

## Context

Today `specfact-cli` serves `docs.specfact.io`, while `specfact-cli-modules` publishes a separate GitHub Pages site under a project-path URL. The two sites are built independently and do not aggregate content during build. As a result, the current public architecture is effectively:

```text
specfact-cli/docs  ------------------> docs.specfact.io
specfact-cli-modules/docs -----------> modules.specfact.io
```

This change defines the core-side target information architecture without requiring a combined docs build:

```text
docs.specfact.io        -> canonical docs entry point / top-level IA
cli.docs.specfact.io    -> core docs origin (specfact-cli)
modules.specfact.io -> modules docs origin (specfact-cli-modules)
```

Cloudflare can later route `docs.specfact.io` either:

- as a lightweight portal that links to the two section sites, or
- as a reverse-proxy entry point for `/core/*` and `/modules/*`

The change in this repository is limited to the core docs contract and content ownership. It does not require Cloudflare automation or reverse-proxy implementation in this repo.

## Goals

- Keep `specfact-cli` as the owner of the canonical docs entry experience and core runtime docs.
- Stop presenting core docs as the long-term canonical source for module-specific workflow content.
- Establish shared navigation vocabulary that both sites can implement consistently.

## Non-Goals

- Build a multi-repository docs artifact in CI
- Replace Jekyll
- Complete every modules-page redirect in one change

## Core Ownership Model

`specfact-cli` owns:

- docs landing/portal language
- core runtime and command-surface docs
- installation and onboarding for the CLI runtime
- marketplace lifecycle concepts, trust, compatibility, and registry behavior
- cross-site docs navigation contract

`specfact-cli` does not own the long-term deep documentation for official bundle workflows once equivalent pages are published in `specfact-cli-modules`.

## Navigation Contract

All public docs experiences should converge on the same top-level labels:

- `Docs Home`
- `Core CLI`
- `Modules`

In `specfact-cli`, those labels should appear in the top navigation and guide readers toward:

- local core-runtime pages for core concerns
- the modules docs site for bundle-specific deep guidance

## Content Strategy In Core

Core-hosted module pages fall into three buckets:

1. Keep as core-owned overview pages
   - pages that explain marketplace concepts, lifecycle, or navigation into module docs
2. Convert to handoff pages
   - short pages that explain the ownership boundary and link to the modules docs canonical page
3. Remove after migration
   - duplicate pages with no remaining core-specific value once redirects/handoffs exist

## Validation Strategy

Implementation should add lightweight regression checks for:

- landing page and README ownership language
- top-level navigation links for docs home/core/modules
- marketplace/reference pages that must distinguish core commands from bundle-delivered commands

These checks are sufficient for this change because the primary output is docs structure and navigation behavior rather than new runtime logic.
