# Capability: core-docs-theme-toggle

## ADDED Requirements

### Requirement: Core docs SHALL support a persisted light/dark theme toggle

Core docs SHALL support a persisted light/dark theme toggle for the docs site shell.

#### Scenario: User toggles theme and preference persists

- **GIVEN** the core docs site is loaded
- **WHEN** a user switches between light and dark theme
- **THEN** the site updates its color theme accordingly
- **AND** the selected preference persists across page reloads

#### Scenario: Theme styling preserves readability for core docs content

- **GIVEN** the core docs include command examples, reference pages, and long-form explanatory content
- **WHEN** the user reads the site in either theme
- **THEN** text, navigation, and code blocks remain readable
- **AND** the shell styling does not obscure canonical links or content hierarchy
