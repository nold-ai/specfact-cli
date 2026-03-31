# Delta: documentation-alignment

Extends the existing `documentation-alignment` capability with core-only site focus and module redirect policy.

## MODIFIED Requirements

### Requirement: Live docs reflect lean-core and grouped bundle command topology

The live authored documentation set SHALL use command examples and migration guidance that match the currently shipped core and bundle command groups, and SHALL NOT present removed or transitional command families as current syntax. The core docs site SHALL focus exclusively on core platform concerns and SHALL redirect module-specific workflow content to modules.specfact.io.

#### Scenario: Core docs site excludes module-specific workflow content

- **GIVEN** the docs.specfact.io landing page (index.md)
- **WHEN** a reader arrives at the docs home
- **THEN** the page clearly separates core platform concerns from module-specific workflows
- **AND** provides direct links to modules.specfact.io for bundle-specific guidance

#### Scenario: Core site landing page delineates core vs modules

- **GIVEN** the docs.specfact.io landing page (index.md)
- **WHEN** a reader arrives at the docs home
- **THEN** the page clearly separates core platform concerns from module-specific workflows
- **AND** provides direct links to modules.specfact.io for bundle-specific guidance

#### Scenario: Getting Started section focuses on platform bootstrap

- **GIVEN** the Getting Started section of the core docs
- **WHEN** a new user follows the getting started path
- **THEN** it covers installation, quickstart, and profiles/IDE setup
- **AND** does NOT include module-specific tutorials as inline content
- **AND** links to modules.specfact.io for module workflow tutorials
