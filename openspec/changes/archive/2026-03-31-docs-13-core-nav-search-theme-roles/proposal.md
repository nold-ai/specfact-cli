# Change: Refine Core Docs UX With Data-Driven Navigation, Search, Theme, And Audience Paths

## Why

The core docs site at `docs.specfact.io` was restructured by `docs-05-core-site-ia-restructure`, handoff pages were cleaned up by `docs-07-core-handoff-conversion`, and validation was added by `docs-12-docs-validation-ci`. But the overall reading experience is still utilitarian and harder to scan than it needs to be. The site lacks client-side search, expertise-guided navigation, theme toggling, and a clearer visual shell for the header/footer and page layout. Users still need to work too hard to answer basic questions like where to start, which pages are beginner-friendly, and how to jump to the right core CLI reference quickly.

The modules docs now have a richer navigation/search/theme model. The core site should follow with a counterpart change tailored to core-platform content so the two sites feel coherent while preserving the core-vs-modules ownership boundary.

## What Changes

- Move core docs sidebar navigation to a data-driven source so navigation structure is easier to evolve without hardcoded layout drift
- Add client-side search for core docs pages using Jekyll-generated search metadata and Lunr.js
- Add expertise and audience-oriented navigation support so users can filter for beginner/intermediate/advanced material and quickly find the right starting path
- Add a light/dark theme toggle with persisted preference and core-doc-friendly styling updates
- Refresh overall page shell with clearer header/footer treatment, cleaner sidebar/content hierarchy, and breadcrumb support where useful
- Update the core landing page so it offers clearer role-based and task-based entry points without reintroducing module-owned content
- Enrich core docs front matter where needed to support search/filter/navigation metadata

## Capabilities

### New Capabilities

- `core-docs-data-driven-nav`: core docs navigation is driven from structured data rather than hardcoded sidebar markup
- `core-docs-client-search`: users can search core docs content from the sidebar/header experience
- `core-docs-expertise-paths`: users can filter and discover core docs by expertise level and entry path
- `core-docs-theme-toggle`: core docs support persisted light/dark theme preference

### Modified Capabilities

- `core-docs-progressive-nav`: the existing progressive core-docs IA is enhanced with richer interaction, filtering, and visual hierarchy
- `documentation-alignment`: the landing and navigation continue to separate core-runtime guidance from module-owned workflow content while improving discoverability

## Impact

- Affected docs: `docs/_layouts/default.html`, `docs/index.md`, core reference/guide/getting-started pages that need search/filter metadata, and footer/header/navigation partials if introduced
- New docs assets likely include data-driven nav config, include partials, and browser-side scripts for search/theme/filter behavior
- Validation follow-up should reuse the existing docs validation change rather than duplicating command/link rules
- Cross-repo alignment: visual/navigation parity should remain compatible with the modules-site UX direction without assuming identical IA or content ownership

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #458
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/458>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: synced
- **Sanitized**: true
