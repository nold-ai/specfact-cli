# core-docs-client-search Specification

## Purpose

TBD - created by archiving change docs-13-core-nav-search-theme-roles. Update Purpose after archive.

## Requirements

### Requirement: Core docs pages SHALL be searchable from a client-side index

Core docs pages SHALL be searchable from the site experience using a client-side index built from repository content.

#### Scenario: Search returns matching core CLI reference pages

- **GIVEN** the core docs site search is available
- **WHEN** a user searches for a known core term such as `init`, `module`, or `architecture`
- **THEN** the results include the corresponding core docs pages
- **AND** the results use core docs metadata and content excerpts from the built site

#### Scenario: Search stays within core-owned docs scope

- **GIVEN** the core docs site search index is generated
- **WHEN** the index is built
- **THEN** it only includes pages owned by the core docs site
- **AND** it does not present module-site pages as if they were local core pages
