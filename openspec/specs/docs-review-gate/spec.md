# docs-review-gate Specification

## Purpose
TBD - created by archiving change docs-04-docs-review-gate-and-link-integrity. Update Purpose after archive.
## Requirements
### Requirement: Docs review validates published route integrity

The docs review gate SHALL derive the published route for authored docs pages from Jekyll front matter and site defaults, and SHALL fail when an internal docs link points to a route that is not published by the current docs source tree.

#### Scenario: Sidebar or landing page links point to an unpublished route

- **WHEN** the docs review gate evaluates links from `docs/index.md` or `docs/_layouts/default.html`
- **THEN** every internal docs route resolves to exactly one published docs page
- **AND** the failure output identifies the authored source and the unresolved route when a link is broken

#### Scenario: Authored markdown links drift from the published permalink

- **WHEN** the docs review gate evaluates internal Markdown links inside published docs pages
- **THEN** links to docs pages resolve by published route rather than only by source-file existence
- **AND** a page with a mismatched permalink fails validation even if the Markdown file still exists on disk

### Requirement: Docs review validates required front matter for published docs targets

The docs review gate SHALL fail when a published docs page that is linked from navigation or another authored docs page is missing required front matter fields needed for publishing and navigation: `layout`, `title`, and `permalink`.

#### Scenario: Linked docs page is missing required metadata

- **WHEN** the docs review gate evaluates a navigation-linked or authored-link target page
- **THEN** the page must declare `layout`, `title`, and `permalink` in front matter
- **AND** the failure output identifies the page and the missing keys

### Requirement: Docs-only pull requests run a dedicated docs review workflow

A dedicated docs review workflow SHALL run the docs review gate for pull requests or pushes that change docs or Markdown content, even when no Python source files changed.

#### Scenario: Docs-only change triggers docs review validation

- **WHEN** a pull request changes only `docs/**` or Markdown files
- **THEN** the dedicated docs review workflow runs the targeted docs review suite
- **AND** docs validation does not wait for the full code-oriented PR orchestrator to complete

