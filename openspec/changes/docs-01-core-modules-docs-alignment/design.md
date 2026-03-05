## Context

The docs set spans the repository README, the published Jekyll site under `docs/`, architecture pages, command references, getting-started guides, adapter guides, and module marketplace guidance. The modularization wave changed the runtime model significantly: the CLI now has a lean core, most workflow commands are grouped under bundle categories, official bundles are installed from the marketplace, and the canonical implementation for extracted modules lives in `specfact-cli-modules`.

The current documentation has three structural risks:
- drift from the former flat command topology,
- duplicated or inconsistent marketplace/module guidance across README, guides, and reference pages,
- no clearly documented ownership boundary for module-specific docs that still live in the core repo.

This is a cross-cutting documentation change rather than a runtime feature. The implementation must cover many Markdown files, but it should still preserve a coherent information architecture: core onboarding and lifecycle concepts remain in `specfact-cli`, while detailed bundle behavior is described in a way that can later move to `specfact-cli-modules` with minimal churn.

## Goals / Non-Goals

**Goals:**
- Establish a documentation contract for the post-modularization architecture.
- Audit and align all user-facing Markdown so command examples, installation flows, and architecture descriptions match current reality.
- Separate core-owned documentation concerns from module/bundle-owned concerns without breaking current docs navigation.
- Make marketplace and bundle docs easy to find and internally consistent.
- Leave explicit migration notes so future docs relocation to `specfact-cli-modules` is expected and documented.

**Non-Goals:**
- No runtime command or packaging behavior changes.
- No immediate move of the docs publishing site from `specfact-cli` to `specfact-cli-modules`.
- No attempt to archive or rewrite historical OpenSpec records.
- No redesign of Jekyll theming beyond required navigation and link fixes.

## Decisions

### Decision: Treat the work as a full docs inventory plus ownership cleanup
A partial doc fix would leave stale pages behind because command and marketplace guidance is spread across many sections. The implementation will therefore inventory all first-party Markdown under `README.md` and `docs/` and classify each page as core-owned, module-owned-but-temporarily-hosted, shared, historical, or generated/vendor.

Alternative considered: update only README, index, and command reference.
Why not chosen: that would not satisfy the user-visible requirement to check every Markdown page and would preserve hidden drift in guides and adapters.

### Decision: Keep core docs as the publication host for now, but explicitly label temporary module-doc hosting
The docs site is still published from this repo, so the immediate change should not move hosting. Instead, module-focused pages will carry a consistent note that the content remains temporarily hosted in core and is intended to migrate to `specfact-cli-modules`.

Alternative considered: move module docs immediately as part of this change.
Why not chosen: that is a larger repo/process migration and would mix documentation alignment with publishing/platform changes.

### Decision: Reframe command docs around ownership and installation source
Command reference and related guides will describe:
- permanent core commands always available in `specfact-cli`,
- grouped bundle commands that appear after marketplace installation,
- per-category and per-package docs instead of a single legacy flat list.

Alternative considered: keep one monolithic command reference and only patch examples.
Why not chosen: it would continue to blur the core-vs-bundle boundary and keep the old mental model alive.

### Decision: Update directory/dependency docs as architecture documentation, not just command help
`docs/reference/directory-structure.md`, `docs/reference/dependency-resolution.md`, module architecture docs, and marketplace docs will be aligned together so readers understand why bundles depend on each other, where code now lives, and which repo owns which artifacts.

Alternative considered: keep dependency and directory docs unchanged because runtime behavior already works.
Why not chosen: those pages are part of the architecture contract and will actively mislead contributors if left in pre-migration form.

### Decision: Add lightweight docs parity validation where practical
If existing tests can be extended cheaply, add or update targeted parity checks for command-surface and docs-ownership expectations.

Alternative considered: rely only on manual review.
Why not chosen: this change exists because manual alignment drifted during a large migration.

## Risks / Trade-offs

- [Scope breadth across many Markdown files] -> Mitigation: inventory files first, explicitly exclude generated `_site` and vendor content, and work category-by-category.
- [Accidentally breaking docs navigation] -> Mitigation: preserve front matter, update sidebar links intentionally, and run markdown/yaml/docs validation after edits.
- [Temporary duplication before module-doc migration] -> Mitigation: use consistent ownership notes and minimize repeated command detail by linking to canonical pages.
- [Confusion between historical references and current guidance] -> Mitigation: leave historical archived OpenSpec artifacts untouched and update only live user-facing docs.

## Migration Plan

1. Create a Markdown inventory for live first-party docs (`README.md`, `docs/**`) and exclude generated/vendor outputs.
2. Classify each document by ownership and migration target.
3. Update top-level entry points first: `README.md`, `docs/index.md`, docs landing/README, marketplace and installation pages.
4. Update command/reference, architecture, directory, and dependency docs to reflect lean core and bundle ownership.
5. Update module-specific guides/adapters/tutorials with temporary hosting notes and corrected command examples.
6. Update navigation and cross-links.
7. Run validation (`openspec validate`, markdown/yaml/docs checks, and any targeted docs parity tests).

Rollback is straightforward: revert the documentation and navigation changes. No runtime or data migration is involved.

## Open Questions

- Should the future module-doc migration target a separate published docs site for `specfact-cli-modules`, or a subsection within the existing docs domain?
- Do we want a generated docs inventory/check manifest in-repo after this pass, or is the OpenSpec task list sufficient?
- Should legacy `docs/reference/commands.md` remain a single page with stronger sections, or split into multiple command-reference pages after the alignment work?
