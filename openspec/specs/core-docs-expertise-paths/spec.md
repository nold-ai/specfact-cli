# core-docs-expertise-paths Specification

## Purpose

TBD - created by archiving change docs-13-core-nav-search-theme-roles. Update Purpose after archive.

## Requirements

### Requirement: Core docs SHALL expose expertise-aware or role-aware entry paths

Core docs SHALL expose expertise-aware or role-aware paths that help users find the right entry points for their current level.

#### Scenario: Expertise filter narrows visible navigation options

- **GIVEN** the core docs navigation includes expertise-aware metadata
- **WHEN** a user selects a specific expertise level
- **THEN** the visible navigation emphasizes pages relevant to that level
- **AND** the selection persists across page loads

#### Scenario: Landing page offers clear entry paths without reintroducing module-owned tutorials

- **GIVEN** the core docs landing page is updated
- **WHEN** a new or returning user arrives at the site
- **THEN** the page highlights clear core-docs starting paths by task or audience
- **AND** any module-specific depth continues to link out to the modules site rather than being duplicated in core
