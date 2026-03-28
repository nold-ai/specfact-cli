## 1. Change Setup And Spec Deltas

- [x] 1.1 Create a dedicated worktree and feature branch from `origin/dev` for `docs-13-core-nav-search-theme-roles`
- [x] 1.2 Run `hatch env create` inside that worktree before implementation
- [x] 1.3 Run pre-flight checks `hatch run smart-test-status` and `hatch run contract-test-status` before changing docs code
- [x] 1.4 Update `openspec/CHANGE_ORDER.md` with `docs-13-core-nav-search-theme-roles`
- [x] 1.5 Add `core-docs-data-driven-nav` capability spec
- [x] 1.6 Add `core-docs-client-search` capability spec
- [x] 1.7 Add `core-docs-expertise-paths` capability spec
- [x] 1.8 Add `core-docs-theme-toggle` capability spec
- [x] 1.9 Extend `core-docs-progressive-nav` / `documentation-alignment` where needed for the new interactive UX layer

## 2. Navigation And Layout

- [x] 2.1 Define a structured navigation data source for the core docs sections created by `docs-05-core-site-ia-restructure`
- [x] 2.2 Replace hardcoded core sidebar navigation with include-driven rendering from that data source
- [x] 2.3 Add breadcrumb or equivalent orientation treatment where it improves core-site navigation clarity
- [x] 2.4 Refine header/footer/page shell styling for a cleaner docs.specfact.io reading experience

## 3. Search, Theme, And Filters

- [x] 3.1 Add a Jekyll-generated search index for core docs pages with title and metadata fields
- [x] 3.2 Add client-side search UX for core docs using the generated index
- [x] 3.3 Add a persisted light/dark theme toggle for the core docs site
- [x] 3.4 Add expertise-level filtering and/or entry-path cues for core docs navigation

## 4. Content Metadata And Landing Page

- [x] 4.1 Enrich affected core docs pages with front matter needed for search and expertise-aware navigation
- [x] 4.2 Update `docs/index.md` so the core landing page gives clearer role-based or task-based entry paths while preserving core-vs-modules ownership boundaries
- [x] 4.3 Ensure any handoff links to modules-owned content remain canonical and do not regress `docs-07-core-handoff-conversion`

## 5. Verification

- [x] 5.1 Run `bundle exec jekyll build` for the core docs site and verify the build stays clean
- [x] 5.2 Verify the data-driven navigation renders correct core sections and links
- [x] 5.3 Verify search returns expected results for known core CLI and architecture keywords
- [x] 5.4 Verify theme toggle and expertise/path selection persist across page loads
- [x] 5.5 Verify docs validation remains green with the new navigation/search assets and enriched front matter
- [x] 5.6 After merge, remove the worktree and clean up the branch-specific Hatch environment
