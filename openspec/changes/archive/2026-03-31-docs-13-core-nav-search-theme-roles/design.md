# Design: Core Docs UX Refactor As A Counterpart To Modules-Site Navigation Improvements

## Summary

This change adds an interactive UX layer to the already-restructured core docs site. It does not revisit the core-vs-modules content boundary established by earlier docs changes. Instead, it improves discoverability and readability through data-driven navigation, client-side search, expertise-aware entry paths, persisted theme selection, and a more coherent page shell.

## Scope Boundaries

- The core site remains focused on platform/runtime concerns
- Module-owned workflow depth remains on `modules.specfact.io`
- Any parity with the modules site is directional, not literal: shared interaction patterns are acceptable, but IA and links remain core-specific
- Existing docs validation and handoff-conversion changes remain the guardrails for cross-site correctness

## UX Goals

- Make it obvious where new users should start
- Reduce friction for experienced users who want command/reference pages quickly
- Improve scanning of the sidebar and landing page
- Support both dark and light reading environments
- Keep the shell visually coherent across the core and modules sites without merging content ownership

## Proposed Building Blocks

- A structured navigation data file describing the existing core-docs IA sections
- Include partials for sidebar rendering, search input/results, expertise or audience filter controls, theme toggle, and optional breadcrumbs
- A Jekyll-generated search index derived from page front matter and content excerpts
- Browser-side scripts for search, theme persistence, and filter behavior
- Front matter enrichment on core pages so they can participate in filtering and search ranking

## Risks And Guardrails

- Search and filters must not expose module-owned pages as if they were core-owned canonical docs
- Landing-page role paths must continue to hand off to modules docs where appropriate instead of recreating module tutorials in core
- Styling refresh should preserve readability and not destabilize the existing Jekyll build/published layout
- Validation should catch broken links or stale navigation references after the refactor
