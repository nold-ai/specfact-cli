# core-docs-data-driven-nav Specification

## Purpose

TBD - created by archiving change docs-13-core-nav-search-theme-roles. Update Purpose after archive.

## Requirements

### Requirement: Core docs navigation SHALL render from structured navigation data

Core docs navigation SHALL be rendered from a structured data source rather than duplicated as hardcoded sidebar markup.

#### Scenario: Sidebar renders from structured core navigation data

- **GIVEN** the core docs site is built
- **WHEN** a user visits a page on `docs.specfact.io`
- **THEN** the sidebar navigation is rendered from a structured data source
- **AND** the rendered sections still reflect the core IA owned by the core docs site

#### Scenario: Navigation updates do not require hardcoded layout edits

- **GIVEN** a core docs section link changes
- **WHEN** the navigation data source is updated
- **THEN** the sidebar rendering reflects the change without duplicating the link structure in hardcoded template markup
